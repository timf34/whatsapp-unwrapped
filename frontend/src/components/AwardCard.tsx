"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { Trophy } from "lucide-react";
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
      initial={{ opacity: 0, y: 30, scale: 0.9 }}
      animate={isInView ? { opacity: 1, y: 0, scale: 1 } : {}}
      transition={{
        delay: delay,
        duration: 0.5,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
      className="flex justify-start mb-3"
    >
      <div className="bg-white rounded-xl shadow-md overflow-hidden max-w-[90%] md:max-w-[75%]">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-400 to-orange-400 px-4 py-3 flex items-center gap-2">
          <Trophy className="w-5 h-5 text-white" />
          <h3 className="font-bold text-white text-sm">{award.title}</h3>
        </div>

        {/* Content */}
        <div className="px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-2xl">🏆</span>
            <span className="font-semibold text-gray-900">{award.recipient}</span>
          </div>

          <p className="text-sm text-gray-700 mb-2 italic">
            &ldquo;{award.evidence}&rdquo;
          </p>

          <p className="text-sm text-gray-500">
            {award.quip}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
