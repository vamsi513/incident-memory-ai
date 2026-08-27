import { NextRequest, NextResponse } from "next/server";

const UPSTREAM = "http://23.21.42.197:8000/v1/search";

export async function POST(req: NextRequest): Promise<NextResponse> {
  try {
    const body = await req.json();

    const upstream = await fetch(UPSTREAM, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await upstream.json();

    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Internal error";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
