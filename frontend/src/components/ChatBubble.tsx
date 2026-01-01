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
}

export default function ChatBubble({
  children,
  sender,
  timestamp,
  status = "read",
  delay = 0,
}: ChatBubbleProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  const isBot = sender === "bot";

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30, scale: 0.95 }}
      animate={isInView ? { opacity: 1, y: 0, scale: 1 } : {}}
      transition={{
        delay: delay,
        duration: 0.4,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
      className={`flex ${isBot ? "justify-start" : "justify-end"} mb-2`}
    >
      <div
        className={`
          relative max-w-[85%] md:max-w-[70%] px-3 py-2 rounded-lg shadow-sm
          ${isBot
            ? "bg-white text-gray-900 rounded-tl-none"
            : "bg-[#dcf8c6] text-gray-900 rounded-tr-none"
          }
        `}
      >
        {/* Message tail */}
        <div
          className={`
            absolute top-0 w-3 h-3
            ${isBot
              ? "-left-2 border-l-8 border-l-transparent border-t-8 border-t-white"
              : "-right-2 border-r-8 border-r-transparent border-t-8 border-t-[#dcf8c6]"
            }
          `}
        />

        {/* Content */}
        <div className="text-sm leading-relaxed break-words">
          {children}
        </div>

        {/* Timestamp and status */}
        <div className={`flex items-center gap-1 justify-end mt-1 -mb-1`}>
          <span className="text-[11px] text-gray-500">{timestamp}</span>
          {!isBot && <StatusIcon status={status} />}
        </div>
      </div>
    </motion.div>
  );
}

function StatusIcon({ status }: { status: MessageStatus }) {
  switch (status) {
    case "sending":
      return <Check className="w-4 h-4 text-gray-400" />;
    case "sent":
      return <Check className="w-4 h-4 text-gray-500" />;
    case "delivered":
      return <CheckCheck className="w-4 h-4 text-gray-500" />;
    case "read":
      return <CheckCheck className="w-4 h-4 text-blue-500" />;
    default:
      return null;
  }
}
