import { NextResponse } from "next/server";

const mockBots = [
  {id: 1, username: "bot1", followers_count: 5000, daily_follows: 50, max_follows: 150, health_score: 95},
  {id: 2, username: "bot2", followers_count: 3000, daily_follows: 30, max_follows: 150, health_score: 88},
  {id: 3, username: "bot3", followers_count: 8000, daily_follows: 80, max_follows: 150, health_score: 92},
];

export async function GET() {
  return NextResponse.json(mockBots);
}
