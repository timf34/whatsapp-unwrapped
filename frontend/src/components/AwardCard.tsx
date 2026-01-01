"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import type { Award } from "@/lib/types";

interface AwardCardProps {
  award: Award;
  delay?: number;
}

export default function AwardCard({ award, delay = 0 }: AwardCardProps) {
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
        {/* Header with gradient */}
        <div className="bg-gradient-to-r from-[#f6b93b] to-[#e58e26] px-4 py-2 flex items-center gap-2">
          <span className="text-lg">🏆</span>
          <h3 className="font-medium text-white text-[14px]">{award.title}</h3>
        </div>

        {/* Content */}
        <div className="p-3">
          {/* Winner */}
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 rounded-full bg-[#dfe5e7] flex items-center justify-center text-sm">
              👤
            </div>
            <span className="font-semibold text-[14px] text-[#111b21]">{award.recipient}</span>
          </div>

          {/* Evidence */}
          <p className="text-[13px] text-[#111b21] mb-2 leading-relaxed">
            {award.evidence}
          </p>

          {/* Quip */}
          <p className="text-[12px] text-[#667781] italic">
            {award.quip}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
