"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import type { InsideJoke } from "@/lib/types";

interface InsideJokeCardProps {
  joke: InsideJoke;
  delay?: number;
}

export default function InsideJokeCard({ joke, delay = 0 }: InsideJokeCardProps) {
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
        {/* Header */}
        <div className="bg-gradient-to-r from-[#667781] to-[#8696a0] px-3 py-1.5 flex items-center gap-2">
          <span className="text-sm">🤫</span>
          <h4 className="font-medium text-white text-[13px]">&quot;{joke.reference}&quot;</h4>
        </div>

        {/* Explanation */}
        <div className="p-3">
          <p className="text-[13px] text-[#667781] leading-relaxed">
            {joke.explanation}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
