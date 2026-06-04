import { NextRequest, NextResponse } from "next/server";

const mockOrders = [
  {id: 1, target_username: "client1", quantity: 500, delivered: 300, status: "processing", price_paid: "25.00"},
  {id: 2, target_username: "client2", quantity: 1000, delivered: 1000, status: "completed", price_paid: "50.00"},
];

let orders = [...mockOrders];

export async function GET() {
  return NextResponse.json(orders);
}

export async function POST(request: NextRequest) {
  const data = await request.json();
  const newOrder = {
    id: orders.length + 1,
    target_username: data.target_username,
    quantity: data.quantity,
    delivered: 0,
    status: "pending",
    price_paid: (data.quantity * 0.05).toFixed(2),
  };
  orders = [newOrder, ...orders];
  return NextResponse.json(newOrder);
}
