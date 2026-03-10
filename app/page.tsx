"use client";
import dynamic from "next/dynamic";
const AgentApp = dynamic(() => import("../components/AgentApp"), { ssr: false });
export default function Page() { return <AgentApp />; }
