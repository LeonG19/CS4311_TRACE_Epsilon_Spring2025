// src/lib/api.ts
export async function fetchTree(project: string)
  : Promise<{ nodes: any[]; edges: any[] }>   // ← add a return type
{
  const res = await fetch(`http://localhost:8000/tree/${encodeURIComponent(project)}`);
  if (!res.ok) throw new Error(`Tree fetch failed: ${res.status}`);
  return res.json();
}