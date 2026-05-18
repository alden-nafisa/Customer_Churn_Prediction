import React, { useState } from "react";
import { Mail, Lock, Activity } from "lucide-react";

export default function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("Admin123");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      onLogin();
    }, 500);
  };

  return (
    <div className="flex h-screen w-full bg-white font-sans overflow-hidden">
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 sm:px-16 md:px-24 xl:px-32 relative z-10">
        <div className="w-full max-w-sm mx-auto">
          <h1 className="text-[32px] font-bold text-slate-900 mb-2 leading-tight tracking-tight">
            Welcome to our Dashboard.
            <br />
            Sign In to see latest
            <br />
            updates.
          </h1>
          <p className="text-slate-400 text-sm mb-12">
            Enter your details to proceed further
          </p>
          <form onSubmit={handleSubmit}>
            <div className="mb-6 relative group">
              <label className="text-[11px] text-slate-400 block mb-1">
                Username
              </label>
              <div className="flex items-center border-b border-slate-200 py-2 group-focus-within:border-indigo-500 transition-colors">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full focus:outline-none text-sm font-bold text-slate-800 bg-transparent"
                />
                <Mail className="text-slate-400 w-4 h-4" />
              </div>
            </div>
            <div className="mb-8 relative group">
              <label className="text-[11px] text-slate-400 block mb-1">
                Password
              </label>
              <div className="flex items-center border-b border-slate-200 py-2 group-focus-within:border-indigo-500 transition-colors">
                <input
                  type="password"
                  placeholder="Start typing..."
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full focus:outline-none text-sm font-medium text-slate-800 bg-transparent placeholder-slate-300"
                />
                <Lock className="text-slate-400 w-4 h-4" />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white text-sm font-semibold py-3.5 rounded-lg hover:bg-indigo-700 transition-colors mb-10 shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Signing In..." : "Sign In"}
            </button>
          </form>
        </div>
      </div>

      {/* Illustration Side */}
      <div className="hidden lg:flex w-1/2 bg-indigo-600 relative items-center justify-center overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-indigo-500/40 rounded-full blur-[80px] -translate-y-1/3 translate-x-1/3"></div>
        <div className="absolute bottom-0 left-0 w-[800px] h-[800px] bg-indigo-700/30 rounded-full blur-[100px] translate-y-1/3 -translate-x-1/4"></div>
        <div className="relative z-10 flex flex-col items-center">
          <div className="w-64 h-64 bg-white/10 backdrop-blur-xl rounded-3xl border border-white/20 p-8 shadow-2xl flex flex-col gap-4 transform hover:scale-105 transition-transform duration-500">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
              <Activity className="text-white" size={24} />
            </div>
            <div className="w-3/4 h-3 bg-white/20 rounded-full mt-4"></div>
            <div className="w-full h-3 bg-white/20 rounded-full"></div>
            <div className="w-5/6 h-3 bg-white/20 rounded-full"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
