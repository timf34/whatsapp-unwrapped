"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import type { Exchange } from "@/lib/types";

interface ExchangeCardProps {
  exchange: Exchange;
  delay?: number;
}

export default function ExchangeCard({ exchange, delay = 0 }: ExchangeCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={isInView ? { opacity: 1, y: 0, scale: 1 } : {}}
      transition={{
        delay: delay,
        duration: 0.35,
        ease: "easeOut",
      }}
      className="mb-2"
    >
      <div className="bg-white rounded-[7.5px] shadow-[0_1px_0.5px_rgba(11,20,26,0.13)] overflow-hidden max-w-[85%] md:max-w-[65%]">
        {/* Context header */}
        <div className="bg-gradient-to-r from-[#00a884] to-[#25d366] px-3 py-1.5">
          <p className="text-white text-[12px]">{exchange.context}</p>
        </div>

        {/* Exchange messages */}
        <div className="p-3 space-y-2">
          {exchange.exchange && exchange.exchange.map((msg, i) => (
            <div key={i} className="flex gap-2">
              <span className="text-[12px] font-semibold text-[#00a884] flex-shrink-0 min-w-[60px]">
                {msg.sender}:
              </span>
              <p className="text-[13px] text-[#111b21]">{msg.text}</p>
            </div>
          ))}

          {/* Punchline */}
          {exchange.punchline && (
            <p className="text-[12px] text-[#667781] italic pt-2 border-t border-[#e9edef]">
              {exchange.punchline}
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}
