"use client";
import { useState } from "react";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Login:", username, password);
  };

  return (
    <div className="min-h-screen bg-neutral-900 flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-neutral-800 p-8 rounded-lg w-96">
        <h1 className="text-2xl text-white mb-6 text-center">SMM Botnet Login</h1>
        <input
          type="text" placeholder="Username" value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full p-3 mb-4 bg-neutral-700 text-white rounded"
        />
        <input
          type="password" placeholder="Password" value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full p-3 mb-4 bg-neutral-700 text-white rounded"
        />
        <button type="submit" className="w-full p-3 bg-blue-600 text-white rounded">
          Login
        </button>
      </form>
    </div>
  );
}
