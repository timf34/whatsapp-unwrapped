"use client";

import { ArrowLeft, MoreVertical, Phone, Video } from "lucide-react";

interface ChatHeaderProps {
  chatName: string;
  participantCount?: number;
}

export default function ChatHeader({ chatName, participantCount }: ChatHeaderProps) {
  return (
    <header className="bg-[#075e54] text-white px-3 py-2 flex items-center gap-3 sticky top-0 z-50">
      <button className="p-1 hover:bg-white/10 rounded-full transition-colors">
        <ArrowLeft className="w-5 h-5" />
      </button>

      {/* Avatar */}
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-lg font-bold">
        🤖
      </div>

      {/* Chat info */}
      <div className="flex-1 min-w-0">
        <h1 className="font-semibold text-base truncate">Unwrapped Bot</h1>
        <p className="text-xs text-emerald-200 truncate">
          Analyzing {chatName}
          {participantCount && ` • ${participantCount} participants`}
        </p>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-1">
        <button className="p-2 hover:bg-white/10 rounded-full transition-colors">
          <Video className="w-5 h-5" />
        </button>
        <button className="p-2 hover:bg-white/10 rounded-full transition-colors">
          <Phone className="w-5 h-5" />
        </button>
        <button className="p-2 hover:bg-white/10 rounded-full transition-colors">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
