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
      className="flex justify-center my-4"
    >
      <span className="bg-white/90 backdrop-blur-sm text-gray-600 text-xs font-medium px-3 py-1 rounded-lg shadow-sm">
        {text}
      </span>
    </motion.div>
  );
}
