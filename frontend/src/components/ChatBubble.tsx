"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Check, CheckCheck } from "lucide-react";
import type { MessageSender, MessageStatus } from "@/lib/types";

interface ChatBubbleProps {
  children: React.ReactNode;
  sender: MessageSender;
  timestamp: string;
  status?: MessageStatus;
  delay?: number;
  showTail?: boolean;
}

export default function ChatBubble({
  children,
  sender,
  timestamp,
  status = "read",
  delay = 0,
  showTail = true,
}: ChatBubbleProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  const isBot = sender === "bot";

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{
        delay: delay,
        duration: 0.3,
        ease: "easeOut",
      }}
      className={`flex ${isBot ? "justify-start" : "justify-end"} mb-[2px] px-[5%] md:px-[63px]`}
    >
      <div
        className={`
          relative max-w-[65%] px-[9px] py-[6px] pb-2
          text-[14.2px] leading-[19px] text-[#111b21]
          ${isBot
            ? "bg-white rounded-[7.5px] rounded-tl-none"
            : "bg-[#d9fdd3] rounded-[7.5px] rounded-tr-none"
          }
          shadow-[0_1px_0.5px_rgba(11,20,26,0.13)]
        `}
      >
        {/* Message tail */}
        {showTail && (
          <span
            className={`
              absolute top-0 w-0 h-0
              ${isBot
                ? "-left-[8px] border-t-[6px] border-t-white border-r-[6px] border-r-white border-b-[6px] border-b-transparent border-l-[6px] border-l-transparent"
                : "-right-[8px] border-t-[6px] border-t-[#d9fdd3] border-r-[6px] border-r-transparent border-b-[6px] border-b-transparent border-l-[6px] border-l-[#d9fdd3]"
              }
            `}
          />
        )}

        {/* Content */}
        <span className="whitespace-pre-wrap break-words">
          {children}
        </span>

        {/* Spacer for timestamp */}
        <span className="inline-block w-[60px] h-[11px]" />

        {/* Timestamp and status - positioned at bottom right */}
        <span className="absolute right-[7px] bottom-[6px] flex items-center gap-[3px] text-[11px] text-[#667781]">
          {timestamp}
          {!isBot && <StatusIcon status={status} />}
        </span>
      </div>
    </motion.div>
  );
}

function StatusIcon({ status }: { status: MessageStatus }) {
  const baseClass = "w-[16px] h-[11px] ml-[2px]";

  switch (status) {
    case "sending":
      return <Check className={`${baseClass} text-[#667781]`} />;
    case "sent":
      return <Check className={`${baseClass} text-[#667781]`} />;
    case "delivered":
      return <CheckCheck className={`${baseClass} text-[#667781]`} />;
    case "read":
      return <CheckCheck className={`${baseClass} text-[#53bdeb]`} />;
    default:
      return null;
  }
}
