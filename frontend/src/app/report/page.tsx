"use client";

import JobCard from "@/components/JobCard";
import styles from "./page.module.css";

const MOCK_JOBS = [
    { company: "Fedora Solutions", role: "Founding Engineer", location: "Remote", salary: "$120k - $150k", postedTime: "today", logoInitial: "F" },
    { company: "Dandy", role: "Business Development Rep", location: "NY • Onsite", salary: "$90k", postedTime: "today", logoInitial: "D" },
    { company: "Hubflo", role: "Growth Marketing Associate", location: "NY • Hybrid", salary: "$70k - $120k", postedTime: "today", logoInitial: "H" },
    { company: "Cura Labs", role: "Founding Engineer (Blockchain)", location: "Remote", salary: "$90k - $170k", postedTime: "today", logoInitial: "C" },
    { company: "Enterprise Mobility", role: "DevOps Manager", location: "San Ramon", salary: "$100k - $120k", postedTime: "today", logoInitial: "E" },
    { company: "TechFlow", role: "Senior React Developer", location: "Austin • Remote", salary: "$140k - $180k", postedTime: "yesterday", logoInitial: "T" },
    { company: "DataMind", role: "AI Research Scientist", location: "SF • Onsite", salary: "$200k+", postedTime: "2 days ago", logoInitial: "D" },
    { company: "GreenEnergy", role: "Product Manager", location: "Berlin • Hybrid", salary: "€80k - €100k", postedTime: "3 days ago", logoInitial: "G" },
    { company: "SecureNet", role: "Cybersecurity Analyst", location: "Remote", salary: "$110k - $140k", postedTime: "4 days ago", logoInitial: "S" },
    { company: "CloudScale", role: "Infrastructure Engineer", location: "Seattle • Onsite", salary: "$150k - $190k", postedTime: "5 days ago", logoInitial: "C" },
];

export default function ReportPage() {
    return (
        <div className={styles.container}>
            <div className={styles.headerContainer}>
                <h1 className={styles.headerTitle}>TOP 10 Jobs From LinkedIn For You</h1>
            </div>

            <div className={styles.jobList}>
                {MOCK_JOBS.map((job, index) => (
                    <JobCard
                        key={index}
                        company={job.company}
                        role={job.role}
                        location={job.location}
                        salary={job.salary}
                        postedTime={job.postedTime}
                        logoInitial={job.logoInitial}
                    />
                ))}
            </div>

            <div className={styles.bottomFade} />
        </div>
    );
}
