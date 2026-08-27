import { NextResponse } from "next/server";
import { API_BASE } from "@/lib/upstream";

const UPSTREAM = `${API_BASE}/v1/facets`;

export async function GET(): Promise<NextResponse> {
  try {
    const upstream = await fetch(UPSTREAM);
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
