"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

interface DateBadgeProps {
  text: string;
  delay?: number;
}

export default function DateBadge({ text, delay = 0 }: DateBadgeProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={isInView ? { opacity: 1, scale: 1 } : {}}
      transition={{
        delay: delay,
        duration: 0.3,
      }}
      className="flex justify-center my-3"
    >
      <span className="bg-[#e1f2fa] text-[#111b21] text-[12.5px] font-normal px-3 py-[6px] rounded-[7.5px] shadow-[0_1px_0.5px_rgba(11,20,26,0.13)]">
        {text}
      </span>
    </motion.div>
  );
}
