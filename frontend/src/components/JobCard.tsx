"use client";

import styles from "./JobCard.module.css";

interface JobCardProps {
    company: string;
    role: string;
    location: string;
    salary: string;
    postedTime: string;
    logoInitial: string;
    url?: string;
    score?: number;
    analysis?: string;
}

export default function JobCard({
    company,
    role,
    location,
    salary,
    postedTime,
    logoInitial,
    url,
    score,
    analysis,
}: JobCardProps) {
    const handleApply = () => {
        // Use provided URL or fallback to LinkedIn search
        const targetUrl =
            url ||
            `https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(
                role + " " + company
            )}`;
        window.open(targetUrl, "_blank");
    };

    return (
        <div className={styles.cardContainer}>
            <div className={styles.leftSection}>
                <div className={styles.logoPlaceholder}>{logoInitial}</div>
                <div className={styles.jobInfo}>
                    <h3 className={styles.roleTitle}>{role}</h3>
                    <span className={styles.companyName}>
                        {company} • {location}
                    </span>
                    <div className={styles.metaData}>
                        <span>{salary}</span>
                        <span>•</span>
                        <span>{postedTime}</span>
                        {score !== undefined && (
                            <>
                                <span>•</span>
                                <span className={styles.matchScore}>
                                    {score.toFixed(0)}% match
                                </span>
                            </>
                        )}
                    </div>
                    {analysis && (
                        <p className={styles.analysis}>{analysis}</p>
                    )}
                </div>
            </div>

            <div className={styles.rightSection}>
                <button className={styles.saveButton}>Save</button>
                <button className={styles.applyButton} onClick={handleApply}>
                    Apply
                </button>
            </div>
        </div>
    );
}
