import json
from neo4j import GraphDatabase
from datetime import datetime
import ssl
import uuid

URI="neo4j://941e739f.databases.neo4j.io"
User="neo4j"
Password="Team_Blue"
class Neo4jInteractive:
    def __init__(self, uri, user, password):
        context = ssl._create_unverified_context()
        # ENCRYPTED and SSL_CONTEXT don't move, they are neccessary for Macs (Mayra in this case at least)
        self.driver = GraphDatabase.driver(uri, auth=(user, password), encrypted=True, ssl_context=context)
            
    # Allows to create a Lead Analyst
    # @params Name: Name of the Analyst, ID: Id of the Analyst
    # @returns JSON with format of all analysts or status error JSON
    def create_Analyst(self, Name, role, initials):
        # if we don't have all the parameters necessary to create an analyst we return a json with error status and erorr Message
        if not all([Name, role, initials]):
            return {"status": "failure", "error":"One or more parameters missing"}
        # initial query to create user
        query="CREATE (u: Analyst {name: $name, initials: $initials}) RETURN elementId(u)"
        
        query_find_role = """
        MERGE (r:Role {role: $role})
        RETURN r
        """
        with self.driver.session() as session:
            # run query with params in safe way using $
            result=session.run(query, name=str(Name), initials=str(initials).upper())
            session.run(query_find_role, role=str(role).capitalize())
            # Depending if is Lead or regular Analyst the permissinons are set
            query_create_relation = """MATCH (u:Analyst {initials: $initials}), (r:Role {role: $role}) MERGE (u)-[:HAS_ROLE]->(r)
                                    SET r.can_lock_unlock= CASE r.role WHEN 'Lead' THEN true ELSE false END, 
                                    r.can_delete = CASE r.role WHEN 'Lead' THEN true ELSE false END,
                                    r.can_create = CASE r.role WHEN 'Lead' THEN true else false END
                                    """
            session.run(query_create_relation, initials=str(initials).upper(), role=str(role).capitalize())
            return {"status": "success"}
    
    # Allows to delete an alayst specifying it's initials
    # @params: initials: Initials of the analyst we are going to delete
    # @returns: JSON format with success or error messages
    def delete_Analyst(self, initials):
        query = """
        MATCH (a:Analyst {initials: $initials})
        DETACH DELETE a
        RETURN COUNT(a) AS deleted_count
        """
        with self.driver.session() as session:
            result = session.run(query, initials=str(initials).upper())
            deleted_count = result.single()["deleted_count"]
        
            if deleted_count > 0:
                return {"status": "success"}
            else:
                return {"status": "failure", "error": "No analyst found"}

    
    
    #Allows to create project with name, id and locked status
    #@params: Project_Name: Name of the project, Lockedstatus: boolean value for locked status
    #         description: Some text to describe the project, MachineIP: the ip associated to that project
    #         status: current status of the project, list_files: list of all the files that the project have
    #@returns: JSON format of with success or error messages
    def create_project(self, Project_Name, lockedstatus, description, MachineIP, status, list_files):
        locked_bool = lockedstatus if isinstance(lockedstatus, bool) else lockedstatus.lower() == "true"
        if not is_ip_valid(MachineIP):
            return {"status": "failure", "error":"Invalid IP"}
        todayDate=datetime.now()
        formatDate = todayDate.strftime("%Y-%m-%dT%H:%M:%S")
        query= """CREATE (p: Project {name: $name, locked:$locked_status, 
                Stamp_Date: datetime($Stamp_Date), description: $description, MachineIP: $MachineIP, Status: $Status, files: $files, last_edit_date: datetime($last_edit), is_deleted:false})"""
        with self.driver.session() as session:
            session.run(query, name=str(Project_Name), locked_status=locked_bool, Stamp_Date=formatDate, description=str(description), MachineIP=str(MachineIP), Status=str(status).capitalize(), files=[]if list_files=="" else list(list_files), last_edit=formatDate)
            return {"status": "success"}
        
    def relationship_results(self, project_name, run_id):
        if not all([project_name, id]):
            return {"status": "failure", "error":"One or more parameters missing"}
        query= """MATCH (p:Project {name: $name}), (s:ScanRun {run_id: $run_id}) MERGE (p)-[:HAS_SCAN]->(s)"""
        with self.driver.session() as session:
            session.run(query, name=str(project_name), run_id=str(run_id))
            return {"status": "success"}


     # Allows to delete a specific project from the DB
    # @params: Project_ID: unique id of project to delete
    # @returns: JSON format of all projects updated
    def delete_project(self, project_name):
        with self.driver.session() as session:
            query = """ MATCH (p:Project {name: $project_name})
                        WHERE p.is_deleted = true
                        DETACH DELETE p
                        UNION
                        MATCH (p:Project {name: $project_name})
                        WHERE p.is_deleted = false
                        SET p.is_deleted = true, p.deleted_date= datetime($delete_date)
                    """
            todayDate=datetime.now()
            formatDate = todayDate.strftime("%Y-%m-%dT%H:%M:%S")
            session.run(query, project_name=project_name, delete_date=formatDate)
            return {"status": "success"}
        
    def restore_project(self, project_name):
        with self.driver.session() as session:
            query= """MATCH (p:Project {name: $project_name}) SET p.is_deleted= false, p.deleted_date=null """
            session.run(query, project_name=project_name)
            return {"status": "success"}

     # Allows the Database to receive a JSON and put all the information inside a node called Results
    # @params: json_data: json object, result_type: indicator for which type of result is
    # @returns: json with success or failure status 
    def process_Response(self, json_data, result_type, project_name, run_id=None):
        if isinstance(json_data, str):
            try:
                results = json.loads(json_data)
            except json.JSONDecodeError:
                return {"status": "failure", "error": "Unsupported type of JSON"}
        elif isinstance(json_data, list):
            results = json_data
        elif isinstance(json_data, dict):
            results = [json_data]
        else:
            return {"status": "failure", "error": "Unsupported type of JSON"}
        
        
        if not run_id:
            run_id = str(uuid.uuid4())

        with self.driver.session() as session:
            try:
                session.execute_write(
                lambda tx: tx.run(
                    """
                    MERGE (s:ScanRun {run_id: $run_id})
                    SET s.type = $type
                    WITH s
                    MATCH (p:Project {name: $project_name})
                    MERGE (p)-[:HAS_SCAN]->(s)
                    """,
                    {"run_id": run_id, "type": result_type, "project_name": project_name}
                    )
                )
                
                for result in results:
                    result["type"] = result_type

                    fields = ", ".join([f"{key}: ${key}" for key in result])
                    query = f"CREATE (r:Result {{ {fields} }})"

                    try:

                        session.execute_write(lambda tx: tx.run(query, result))

                        session.execute_write(lambda tx: tx.run(
                            """ MATCH (s:ScanRun {run_id: $run_id}), (r:Result {id: $result_id})
                            MERGE (s)-[:HAS_RESULT]->(r)""",{"run_id": run_id, "result_id": result["id"]}))
                        
                        self.relationship_results(project_name, run_id)
                    except Exception as e:
                        return {
                            "status": "failure",
                            "error": f"Failed to insert record: {str(e)}"
                        }

            except Exception as e:
                return {
                    "status": "failure",
                    "error": f"Failed to insert record: {str(e)}"
                    }

        return {"status": "success"}
    

    def export_project(self, project_name):
        """
        Exports a project's data including its properties, associated analysts, and results.
        
        Args:
            project_name (str): Name of the project to export
            
        Returns:
            dict: JSON-compatible dictionary containing project data, analysts, and results
        """
        with self.driver.session() as session:
            # Query to get project details, owning analyst, participating analysts, and results
            query = """
            MATCH (p:Project {name: $project_name})
            OPTIONAL MATCH (p)<-[:OWNS]-(owner:Analyst)
            OPTIONAL MATCH (p)<-[:inProject]-(participant:Analyst)
            OPTIONAL MATCH (p)-[:HAS_RESULT]->(r:Result)
            RETURN p, 
                   collect(DISTINCT owner) AS owners,
                   collect(DISTINCT participant) AS participants,
                   collect(DISTINCT r) AS results
            """
            result = session.run(query, project_name=project_name)
            record = result.single()
            
            if not record:
                return {"status": "failure", "error": "Project not found"}
                
            project_data = dict(record["p"])
            owners = [dict(owner) for owner in record["owners"]]
            participants = [dict(participant) for participant in record["participants"]]
            results = [dict(result) for result in record["results"]]
            
            # Structure the export data
            export_data = {
                "project": {
                    "name": project_data.get("name"),
                    "locked": project_data.get("locked"),
                    "stamp_date": project_data.get("Stamp_Date"),
                    "description": project_data.get("description"),
                    "machine_ip": project_data.get("MachineIP"),
                    "status": project_data.get("Status"),
                    "files": project_data.get("files", []),
                    "last_edit_date": project_data.get("last_edit_date"),
                    "is_deleted": project_data.get("is_deleted", False),
                    "deleted_date": project_data.get("deleted_date")
                },
                "owners": [{
                    "name": owner.get("name"),
                    "initials": owner.get("initials")
                } for owner in owners],
                "participants": [{
                    "name": participant.get("name"),
                    "initials": participant.get("initials")
                } for participant in participants],
                "results": results
            }
            
            return {
                "status": "success",
                "data": export_data
            }




            
    #Allows to join to an existing project
    #@params: project_name: Name of the project to join, analystInitials: Initials of the analyst that will join the project
    #@returns: JSON format with success or error messages
    def join_project(self, project_name, analystInitials):
        query = """
        MATCH (a:Analyst {initials: $initials}), (p:Project {name: $name})
        MERGE (a)-[:inProject]->(p)
        RETURN COUNT(a) AS analysts_joined
        """
        with self.driver.session() as session:
            result = session.run(query, initials=str(analystInitials).upper(), name=str(project_name))
            analysts_joined = result.single()["analysts_joined"]

            if analysts_joined > 0:
                return {"status": "success"}
            else:
                return {"status": "failure", "error": "No analysts or project not found"}
    # Allows to create a folder(node) to store projects
    # @params: path: string with the path or name for the folder
    # @returns: JSON with success or failure status        
    def create_folder(self, path):
        todayDate=datetime.now()
        formatDate = todayDate.strftime("%Y-%m-%dT%H:%M:%S")
        if not path:
            return {"status":"failure", "error": "No name received"}
        query="""CREATE (:Folder {path:$path,  creation_date:datetime($creation_date)})"""
        with self.driver.session() as session:
            session.run(query, path=str(path), creation_date=formatDate)
            return {"status": "success"}
  
    def get_folders(self):
        query="MATCH (f:Folder) RETURN f"
        with self.driver.session() as session:
            result=session.run(query)
            return [dict(record["f"]) for record in result]
    
    def add_project_to_folder(self, project_name, folder_path):
        if not all([project_name, folder_path]):
            return {"status": "failure", "error": "No project or folder received"}
        query= """MATCH (u:Project {name: $name}), (f:Folder{path:$folder_path}) 
                MERGE (u)-[:IS_IN]->(f)"""
        try:
            with self.driver.session() as session:
                session.run(query, name=str(project_name), folder_path=str(folder_path))
                return {"status": "success"}
        except Exception as e:
            return {"status": "failure", "error": f"Failed to insert record: {str(e)}"}
        
    def get_projects_in_folder(self, folder_name):
        if not folder_name:
            return {"status": "failure", "error": "No folder name provided"}

        query = """
        MATCH (p:Project)-[:IS_IN]->(f:Folder {name: $folder_name})
        RETURN p.name AS project_name
        """

        try:
            with self.driver.session() as session:
                result = session.run(query, folder_name=str(folder_name))
                projects = [dict(record["project_name"]) for record in result]
                return projects
        except Exception as e:
            return {"status": "failure", "error": str(e)}

        
    # Allows to add a relationship of ownership betwwen the analyst and a project
    # @params: Owner_initials: Initials of the Lead analyst, project_name: Name of the project the analyst os going to own
    # @returns: JSON format of all relationships
    def add_ownership(self, Owner_initials, project_name):
        query=""" MATCH (u:Analyst {initials: $initials})-[:HAS_ROLE]->(r:Role {role: "Lead"})
                MATCH (p:Project {name: $project})
                WHERE NOT (p)<-[:OWNS]-(:Analyst)
                MERGE (u)-[o:OWNS]->(p)
                RETURN o
                """
        with self.driver.session() as session:
            session.run(query, initials=str(Owner_initials), project=str(project_name))
            result=session.run("MATCH p=()-[]->() RETURN p")
            for record in result:
                if record is None:
                    return {"status":"failure","error":"Proyect or Analyst does not exist or already has an owner"}
            return {"status":"success",}
        
        
    # Allows to change locked property of a project to true
    # @params: Project_ID: Unique id of project to lock
    # @returns: JSON format of the locked project     
    def lock_projects(self, project_name, analyst_initials):
        with self.driver.session() as session:
            lock = "MATCH (p:Project {name: $name})<-[:OWNS]-(a:Analyst {initials: $initials})-[:HAS_ROLE]->(r:Role) WHERE r.role = 'Lead' AND r.can_lock_unlock = true SET p.locked = true SET p.Status= 'Inactive' RETURN count(p) AS projectsLocked"
            result=session.run(lock, name = project_name, initials=str(analyst_initials).upper())
            if result.single().get("projectLocked"):
                return {"status":"success"}
            else:
                return {"status":"failure", "error": "You cannot lock this project, please contact a Lead"}
            
    # Allows to change the locked property of a project to false
    # @params: Project_ID: Unique id of project to lock
    # @returns: Json format of unlocked project
    def unlock_projects(self, project_name, analyst_initials):
        with self.driver.session() as session:
            lock = "MATCH (p:Project {name: $name})<-[:OWNS]-(a:Analyst {initials: $initials})-[:HAS_ROLE]->(r:Role) WHERE r.role = 'Lead' AND r.can_lock_unlock = true SET p.locked = false SET p.Status= 'Active' RETURN count(p) AS projectsLocked"
            result=session.run(lock, name=project_name, initials=str(analyst_initials).upper())
            if result.single().get("projectLocked"):
                return {"status":"success"}
            else:
                return {"status":"failure", "error": "You cannot lock this project, please contact a Lead"}
            
    # Allows to add a list of files into the files property of a project node
    # @params: project_name: name of the project we want to add files, files: list of files to add into the project
    # @returns:JSON format with status
    def add_placeholderfiles(self, project_name, files):
        with self.driver.session() as session:
            query= """MATCH (p:Project {name: $project}) 
            SET p.files=$file_list
            RETURN p.id AS id, p.name AS name, p.locked AS locked, p.files AS files"""
            session.run(query, project=project_name, file_list=files)
            return {"status":"success"}

    # added the following to match project manager file ↓
    def get_project_by_name(self, name):
        query = """
        MATCH (p:Project {name: $name})
        RETURN p
        """
        with self.driver.session() as session:
            result = session.run(query, name=name)
            return [dict(record) for record in result]
    
    def check_login(self, analyst_initials):
        query=""" MATCH (u:Analyst {initials: $analyst_initials})
                RETURN COUNT(u) AS successLogIn"""
        with self.driver.session() as session:
            result= session.run(query, analyst_initials=str(analyst_initials).upper())
            check= result.single()["successLogIn"]
            if check > 0:
                return {"status": "success"}
            else:
                return {"status":"failure", "error":"No analyst with initials"}

     # Retreives all  the analysts in the database 
    # @params: no parameters
    # @returns: JSON format of all the Analysts 
    def print_Analyst(self):
        query = """
        MATCH (u:Analyst)
        RETURN u
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record["u"]) for record in result]
        

    def get_project(self, project_name):
        query = """
        MATCH (p:Project {name: $project_name})<-[:OWNS]-(u:Analyst)
        RETURN p, u.name AS lead_analyst_initials
        """
        with self.driver.session() as session:
            records = session.run(query, project_name=project_name)
            record = records.single()
            if record:
                p = record["p"]
                info = dict(p)
                info["lead_analyst_initials"] = record["lead_analyst_initials"]
                return info
            return {"status": "failure", "error":"Project with that name does not exist"}
    # get all projects to print
    def get_all_projects(self):
        query = """
        MATCH (a:Analyst)-[:OWNS]->(p:Project)
        RETURN p, a.initials AS analyst_initials
        """
        with self.driver.session() as session:
            result = session.run(query)
            projects=[{**dict(record["p"]),"analyst_initials": record["analyst_initials"]}for record in result]
            return projects
        
        
    # get all projects the analyst owns
    def get_my_projects(self, analyst_initials):
        query = """
        MATCH (u:Analyst {initials: $initials})-[:OWNS]->(p:Project)
        RETURN p, u.initials AS analyst_initials
        """
        with self.driver.session() as session:
            result = session.run(query, initials=str(analyst_initials).upper())
            return [{**dict(record["p"]), "analyst_initials":record["analyst_initials"]} for record in result]
    
    def get_Analyst(self):
        query="MATCH (a:Analyst) RETRUN a"
        with self.driver.session() as session:
            result= session.run(query)
            return [dict(record["a"]) for record in result]

    def get_shared_projects(self, analyst_initials):
        query = """
        MATCH (other:Analyst)-[:OWNS]->(p:Project)
        WHERE other.name <> $initials
        RETURN p
        """
        with self.driver.session() as session:
            result = session.run(query, initials=analyst_initials)
            return [dict(record["p"]) for record in result]

    
def is_ip_valid(ip):
    parts = ip.split(".")  
    if len(parts) != 4:  
        return False
    
    for part in parts:
        if not part.isdigit():  
            return False
        
        num = int(part)
        if num < 0 or num > 255: 
            return False
        
        if part != str(num):
            return False
    
    return True
