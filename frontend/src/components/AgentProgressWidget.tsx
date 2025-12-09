"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./AgentProgressWidget.module.css";

interface AgentTask {
    id: string;
    label: string;
    status: "pending" | "processing" | "completed";
}

export default function AgentProgressWidget() {
    const router = useRouter();
    const [progress, setProgress] = useState(0);
    const [tasks, setTasks] = useState<AgentTask[]>([
        { id: "1", label: "Analyzing search intent", status: "pending" },
        { id: "2", label: "Retrieving data sources", status: "pending" },
        { id: "3", label: "Processing information", status: "pending" },
        { id: "4", label: "Generating response", status: "pending" },
    ]);

    useEffect(() => {
        const totalDuration = 10000; // 10 seconds
        const steps = 100;
        const intervalTime = totalDuration / steps;

        let currentProgress = 0;

        // Task timing breakpoints (approximate)
        // 0-25%: Task 1
        // 25-50%: Task 2
        // 50-75%: Task 3
        // 75-100%: Task 4

        const updateTasks = (prog: number) => {
            if (prog < 25) {
                setTasks(prev => prev.map(t =>
                    t.id === "1" ? { ...t, status: "processing" } : t));
            } else if (prog === 25) {
                setTasks(prev => prev.map(t =>
                    t.id === "1" ? { ...t, status: "completed" } :
                        t.id === "2" ? { ...t, status: "processing" } : t));
            } else if (prog === 50) {
                setTasks(prev => prev.map(t =>
                    t.id === "2" ? { ...t, status: "completed" } :
                        t.id === "3" ? { ...t, status: "processing" } : t));
            } else if (prog === 75) {
                setTasks(prev => prev.map(t =>
                    t.id === "3" ? { ...t, status: "completed" } :
                        t.id === "4" ? { ...t, status: "processing" } : t));
            } else if (prog >= 100) {
                setTasks(prev => prev.map(t =>
                    t.id === "4" ? { ...t, status: "completed" } : t));
            }
        };

        const interval = setInterval(() => {
            currentProgress += 1;
            setProgress(currentProgress);
            updateTasks(currentProgress);

            if (currentProgress >= 100) {
                clearInterval(interval);
                // Navigate to Report page
                setTimeout(() => {
                    router.push("/report");
                }, 500); // Slight delay for visual completion
            }
        }, intervalTime);

        return () => clearInterval(interval);
    }, [router]);

    return (
        <div className={styles.container}>
            {/* Progress Card */}
            <div className={styles.glassCard}>
                <div className={styles.glassEffectLayer1} />
                <div className={styles.progressHeader}>
                    <span>Progress</span>
                    <span className={styles.percentage}>{progress}%</span>
                </div>
                <div className={styles.progressBarContainer}>
                    <div
                        className={styles.progressBarFill}
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Task List Card */}
            <div className={styles.glassCard}>
                <div className={styles.glassEffectLayer1} />
                <div className={styles.taskList}>
                    {tasks.map((task) => (
                        <div
                            key={task.id}
                            className={`${styles.taskItem} ${styles[task.status]}`}
                        >
                            <div className={styles.iconContainer}>
                                {task.status === "completed" && (
                                    <svg className={styles.checkIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                )}
                                {task.status === "processing" && (
                                    <div className={styles.spinner} />
                                )}
                                {task.status === "pending" && (
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#334155" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <circle cx="12" cy="12" r="10"></circle>
                                    </svg>
                                )}
                            </div>
                            <span>{task.label}</span>
                        </div>
                    ))}
                </div>

                {tasks.some(t => t.status === "processing") && (
                    <div className={styles.statusText}>Searching for the most relevant content...</div>
                )}
            </div>
        </div>
    );
}
