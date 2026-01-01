"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

interface FunnyMomentCardProps {
  moment: string;
  delay?: number;
}

export default function FunnyMomentCard({ moment, delay = 0 }: FunnyMomentCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: -20 }}
      animate={isInView ? { opacity: 1, x: 0 } : {}}
      transition={{
        delay: delay,
        duration: 0.3,
        ease: "easeOut",
      }}
      className="mb-1.5"
    >
      <div className="bg-white rounded-[7.5px] shadow-[0_1px_0.5px_rgba(11,20,26,0.13)] px-3 py-2 max-w-[85%] md:max-w-[65%]">
        <div className="flex gap-2 items-start">
          <span className="text-sm flex-shrink-0">😂</span>
          <p className="text-[13px] text-[#111b21] leading-relaxed">
            {moment}
          </p>
        </div>
      </div>
    </motion.div>
  );
}
