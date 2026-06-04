"use client";
import { useState, useEffect } from "react";

interface Order {
  id: number;
  target_username: string;
  quantity: number;
  delivered: number;
  status: string;
  price_paid: string | number;
}

interface Bot {
  id: number;
  username: string;
  followers_count: number;
  daily_follows: number;
  max_follows: number;
  health_score: number;
}

export default function Home() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [bots, setBots] = useState<Bot[]>([]);
  const [target, setTarget] = useState("");
  const [quantity, setQuantity] = useState(100);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    fetch("/api/orders")
      .then(r => r.json())
      .then(setOrders)
      .catch(() => setOrders([
        {id: 1, target_username: "client1", quantity: 500, delivered: 300, status: "processing", price_paid: "25.00"},
        {id: 2, target_username: "client2", quantity: 1000, delivered: 1000, status: "completed", price_paid: "50.00"},
      ]));
    
    fetch("/api/bots")
      .then(r => r.json())
      .then(setBots)
      .catch(() => setBots([
        {id: 1, username: "bot1", followers_count: 5000, daily_follows: 50, max_follows: 150, health_score: 95},
        {id: 2, username: "bot2", followers_count: 3000, daily_follows: 30, max_follows: 150, health_score: 88},
        {id: 3, username: "bot3", followers_count: 8000, daily_follows: 80, max_follows: 150, health_score: 92},
      ]));
  }, []);

  const createOrder = () => {
    fetch("/api/orders", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({target_username: target, quantity})
    }).then(r => r.json()).then(newOrder => {
      setOrders([newOrder, ...orders]);
      setTarget("");
    });
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">SMM Botnet - Instagram Follower Reseller</h1>
        <p className="mb-6 text-green-400">WebSocket: {connected ? "Connected" : "Disconnected"}</p>
        
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <div className="bg-slate-800 p-4 rounded">
            <h2 className="text-xl mb-2">Total Orders</h2>
            <p className="text-4xl font-bold">{orders.length}</p>
          </div>
          <div className="bg-slate-800 p-4 rounded">
            <h2 className="text-xl mb-2">Completed</h2>
            <p className="text-4xl font-bold text-green-400">{orders.filter(o => o.status === "completed").length}</p>
          </div>
          <div className="bg-slate-800 p-4 rounded">
            <h2 className="text-xl mb-2">Active Bots</h2>
            <p className="text-4xl font-bold text-blue-400">{bots.filter(b => b.health_score > 70).length}</p>
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-lg mb-8">
          <h2 className="text-2xl mb-4">New Order</h2>
          <div className="flex gap-4">
            <input
              placeholder="Target username"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              className="flex-1 p-3 bg-slate-700 rounded"
            />
            <input
              type="number"
              placeholder="Quantity"
              value={quantity}
              onChange={(e) => setQuantity(parseInt(e.target.value) || 100)}
              className="w-32 p-3 bg-slate-700 rounded"
            />
            <button onClick={createOrder} className="px-6 py-3 bg-blue-600 rounded hover:bg-blue-700">
              Create
            </button>
          </div>
          <p className="mt-2 text-sm text-slate-400">Est. Price: ${(quantity * 0.05).toFixed(2)}</p>
        </div>

        <div className="bg-slate-800 p-6 rounded-lg mb-8">
          <h2 className="text-2xl mb-4">Bots Status</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {bots.map(bot => (
              <div key={bot.id} className="bg-slate-700 p-4 rounded">
                <p className="font-bold">@{bot.username}</p>
                <p>Followers: {bot.followers_count}</p>
                <p>Today: {bot.daily_follows}/{bot.max_follows}</p>
                <p>Health: <span className={bot.health_score > 70 ? "text-green-400" : "text-yellow-400"}>{bot.health_score}</span></p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 p-6 rounded-lg">
          <h2 className="text-2xl mb-4">Orders</h2>
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left p-2">ID</th>
                <th className="text-left p-2">Target</th>
                <th className="text-left p-2">Progress</th>
                <th className="text-left p-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(order => (
                <tr key={order.id} className="border-b border-slate-700">
                  <td className="p-2">#{order.id}</td>
                  <td className="p-2">@{order.target_username}</td>
                  <td className="p-2">
                    <div className="w-full bg-slate-700 rounded h-2">
                      <div className="bg-blue-500 h-2 rounded" style={{width: `${(order.delivered/order.quantity)*100}%`}} />
                    </div>
                  </td>
                  <td className="p-2">{order.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
