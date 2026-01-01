"use client";

import { Search, MoreVertical } from "lucide-react";

interface ChatHeaderProps {
  chatName: string;
  participantCount?: number;
}

export default function ChatHeader({ chatName, participantCount }: ChatHeaderProps) {
  return (
    <header className="bg-[#ededed] h-[60px] min-h-[60px] px-4 flex items-center justify-between z-10">
      {/* Left section - Avatar and info */}
      <div className="flex items-center flex-1 min-w-0">
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-[#dfe5e7] flex items-center justify-center mr-3 flex-shrink-0">
          <span className="text-xl">🤖</span>
        </div>

        {/* Chat info */}
        <div className="flex-1 min-w-0">
          <h1 className="text-[#111b21] font-normal text-base truncate">
            Unwrapped Bot
          </h1>
          <p className="text-[#667781] text-xs truncate">
            {chatName}
            {participantCount && ` · ${participantCount} participants`}
          </p>
        </div>
      </div>

      {/* Right section - Actions */}
      <div className="flex items-center gap-6 mr-2">
        <button className="text-[#54656f] hover:text-[#3b4a54] transition-colors">
          <Search className="w-5 h-5" />
        </button>
        <button className="text-[#54656f] hover:text-[#3b4a54] transition-colors">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>
    </header>
  );
}
