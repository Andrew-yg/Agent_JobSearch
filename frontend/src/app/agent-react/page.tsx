"use client";

import AgentProgressWidget from "@/components/AgentProgressWidget";
import styles from "./page.module.css";

export default function AgentReactPage() {
    return (
        <div className={styles.container}>
            <AgentProgressWidget />
        </div>
    );
}
