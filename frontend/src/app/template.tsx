"use client";

import { motion, AnimatePresence } from "framer-motion";

export default function Template({ children }: { children: React.ReactNode }) {
    return (
        <AnimatePresence mode="wait">
            <motion.div
                initial={{ x: "100%", opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: "-100%", opacity: 0 }}
                transition={{ ease: "easeInOut", duration: 0.5 }}
                style={{ width: "100%", height: "100%", position: "absolute" }}
            >
                {children}
            </motion.div>
        </AnimatePresence>
    );
}
