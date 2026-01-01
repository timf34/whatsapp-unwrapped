"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import type { Contradiction } from "@/lib/types";

interface ContradictionCardProps {
  contradiction: Contradiction;
  delay?: number;
}

export default function ContradictionCard({ contradiction, delay = 0 }: ContradictionCardProps) {
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
        {/* Header with person name */}
        <div className="bg-gradient-to-r from-[#ea4c89] to-[#f472b6] px-3 py-1.5 flex items-center gap-2">
          <span className="text-sm">🤔</span>
          <h4 className="font-medium text-white text-[13px]">{contradiction.person}</h4>
        </div>

        {/* Content */}
        <div className="p-3 space-y-2">
          {/* What they said */}
          <div className="flex gap-2">
            <span className="text-[11px] bg-[#e7f8e9] text-[#25d366] px-1.5 py-0.5 rounded font-medium flex-shrink-0">
              SAYS
            </span>
            <p className="text-[13px] text-[#111b21]">&quot;{contradiction.says}&quot;</p>
          </div>

          {/* What they did */}
          <div className="flex gap-2">
            <span className="text-[11px] bg-[#fce4ec] text-[#ea4c89] px-1.5 py-0.5 rounded font-medium flex-shrink-0">
              DOES
            </span>
            <p className="text-[13px] text-[#111b21]">{contradiction.does}</p>
          </div>

          {/* Punchline */}
          {contradiction.punchline && (
            <p className="text-[12px] text-[#667781] italic pt-1 border-t border-[#e9edef]">
              {contradiction.punchline}
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}
