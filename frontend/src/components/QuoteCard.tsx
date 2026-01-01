"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import type { Quote } from "@/lib/types";

interface QuoteCardProps {
  quote: Quote;
  delay?: number;
}

export default function QuoteCard({ quote, delay = 0 }: QuoteCardProps) {
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
        {/* Quote content */}
        <div className="p-3">
          {/* The quote itself */}
          <div className="flex gap-2 mb-2">
            <span className="text-[#25d366] text-xl leading-none">&ldquo;</span>
            <p className="text-[14px] text-[#111b21] leading-relaxed flex-1">
              {quote.text}
            </p>
            <span className="text-[#25d366] text-xl leading-none self-end">&rdquo;</span>
          </div>

          {/* Author */}
          <div className="flex items-center gap-2 mb-2">
            <div className="w-6 h-6 rounded-full bg-[#dfe5e7] flex items-center justify-center text-xs">
              👤
            </div>
            <span className="font-semibold text-[13px] text-[#111b21]">— {quote.author}</span>
          </div>

          {/* Context/Commentary */}
          {quote.context && (
            <p className="text-[12px] text-[#667781] italic pl-2 border-l-2 border-[#25d366]">
              {quote.context}
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}
