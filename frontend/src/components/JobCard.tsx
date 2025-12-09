"use client";

import styles from "./JobCard.module.css";

interface JobCardProps {
    company: string;
    role: string;
    location: string;
    salary: string;
    postedTime: string;
    logoInitial: string;
}

export default function JobCard({ company, role, location, salary, postedTime, logoInitial }: JobCardProps) {

    const handleApply = () => {
        // Mock navigation to LinkedIn
        window.open(`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(role + " " + company)}`, '_blank');
    };

    return (
        <div className={styles.cardContainer}>
            <div className={styles.leftSection}>
                <div className={styles.logoPlaceholder}>
                    {logoInitial}
                </div>
                <div className={styles.jobInfo}>
                    <h3 className={styles.roleTitle}>{role}</h3>
                    <span className={styles.companyName}>{company} • {location}</span>
                    <div className={styles.metaData}>
                        <span>{salary}</span>
                        <span>•</span>
                        <span>{postedTime}</span>
                    </div>
                </div>
            </div>

            <div className={styles.rightSection}>
                <button className={styles.saveButton}>Save</button>
                <button className={styles.applyButton} onClick={handleApply}>Apply</button>
            </div>
        </div>
    );
}
