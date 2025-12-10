"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./AgentProgressWidget.module.css";

interface AgentTask {
    id: string;
    label: string;
    status: "pending" | "processing" | "completed" | "error";
}

interface SearchParams {
    resumeId: string;
    keywords: string;
    location: string;
    experience: string;
    postedTime: string;
    jobType: string;
}

const API_BASE = "http://localhost:8000/api";

export default function AgentProgressWidget() {
    const router = useRouter();
    const [progress, setProgress] = useState(0);
    const [currentMessage, setCurrentMessage] = useState("Initializing...");
    const [tasks, setTasks] = useState<AgentTask[]>([
        { id: "1", label: "Initializing browser", status: "pending" },
        { id: "2", label: "Searching LinkedIn jobs", status: "pending" },
        { id: "3", label: "Analyzing matches with AI", status: "pending" },
        { id: "4", label: "Scoring and ranking", status: "pending" },
    ]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const startSearch = async () => {
            // Get search params from sessionStorage
            const paramsStr = sessionStorage.getItem("searchParams");
            if (!paramsStr) {
                setError("No search parameters found. Please go back and try again.");
                return;
            }

            const params: SearchParams = JSON.parse(paramsStr);

            try {
                // Start SSE connection
                const response = await fetch(`${API_BASE}/search`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        resume_id: params.resumeId,
                        keywords: params.keywords,
                        location: params.location,
                        experience: params.experience,
                        posted_time: params.postedTime,
                        job_type: params.jobType,
                    }),
                });

                if (!response.ok) {
                    throw new Error("Search request failed");
                }

                const reader = response.body?.getReader();
                const decoder = new TextDecoder();

                if (!reader) {
                    throw new Error("No response stream");
                }

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const text = decoder.decode(value);
                    const lines = text.split("\n");

                    for (const line of lines) {
                        if (line.startsWith("data: ")) {
                            const data = line.slice(6);

                            if (data === "[DONE]") {
                                // Search complete, navigate to report
                                setTimeout(() => {
                                    router.push("/report");
                                }, 500);
                                return;
                            }

                            try {
                                const parsed = JSON.parse(data);

                                if (parsed.type === "result") {
                                    // Store results for report page
                                    sessionStorage.setItem(
                                        "searchResults",
                                        JSON.stringify(parsed.data)
                                    );
                                    setProgress(100);
                                    setTasks((prev) =>
                                        prev.map((t) => ({
                                            ...t,
                                            status: "completed",
                                        }))
                                    );
                                } else {
                                    // Progress update
                                    const step = parsed.step || 1;
                                    const totalSteps = parsed.total || 4;
                                    const newProgress = Math.round(
                                        (step / totalSteps) * 100 -
                                        (parsed.status === "processing" ? 10 : 0)
                                    );
                                    setProgress(Math.max(progress, newProgress));
                                    setCurrentMessage(parsed.message || "Processing...");

                                    // Update task statuses
                                    setTasks((prev) =>
                                        prev.map((t, idx) => {
                                            if (idx + 1 < step) {
                                                return { ...t, status: "completed" };
                                            } else if (idx + 1 === step) {
                                                return {
                                                    ...t,
                                                    status:
                                                        parsed.status === "completed"
                                                            ? "completed"
                                                            : parsed.status === "error"
                                                                ? "error"
                                                                : "processing",
                                                };
                                            }
                                            return t;
                                        })
                                    );

                                    if (parsed.status === "error") {
                                        setError(parsed.message);
                                    }
                                }
                            } catch (e) {
                                // Ignore parse errors for incomplete chunks
                            }
                        }
                    }
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : "An error occurred");
            }
        };

        startSearch();
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
                                    <svg
                                        className={styles.checkIcon}
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="3"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <polyline points="20 6 9 17 4 12"></polyline>
                                    </svg>
                                )}
                                {task.status === "processing" && (
                                    <div className={styles.spinner} />
                                )}
                                {task.status === "error" && (
                                    <svg
                                        width="20"
                                        height="20"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="#ef4444"
                                        strokeWidth="2"
                                    >
                                        <circle cx="12" cy="12" r="10" />
                                        <line x1="15" y1="9" x2="9" y2="15" />
                                        <line x1="9" y1="9" x2="15" y2="15" />
                                    </svg>
                                )}
                                {task.status === "pending" && (
                                    <svg
                                        width="20"
                                        height="20"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="#334155"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <circle cx="12" cy="12" r="10"></circle>
                                    </svg>
                                )}
                            </div>
                            <span>{task.label}</span>
                        </div>
                    ))}
                </div>

                {!error && tasks.some((t) => t.status === "processing") && (
                    <div className={styles.statusText}>{currentMessage}</div>
                )}

                {error && (
                    <div className={styles.statusText} style={{ color: "#ef4444" }}>
                        Error: {error}
                    </div>
                )}
            </div>
        </div>
    );
}
