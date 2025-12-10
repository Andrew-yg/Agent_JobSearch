"use client";

import { useEffect, useState } from "react";
import JobCard from "@/components/JobCard";
import styles from "./page.module.css";

interface ScoredJob {
    job: {
        id: string;
        title: string;
        company: string;
        location: string;
        salary: string | null;
        posted_time: string;
        description: string;
        url: string;
        logo_initial: string;
    };
    overall_score: number;
    skill_match: number;
    experience_match: number;
    education_match: number;
    analysis: string;
}

interface SearchResult {
    resume_id: string;
    total_jobs_found: number;
    top_jobs: ScoredJob[];
    search_time_seconds: number;
}

// Fallback mock data if no real results
const MOCK_JOBS = [
    {
        company: "Fedora Solutions",
        role: "Founding Engineer",
        location: "Remote",
        salary: "$120k - $150k",
        postedTime: "today",
        logoInitial: "F",
        url: "",
        score: 95,
    },
    {
        company: "Dandy",
        role: "Business Development Rep",
        location: "NY • Onsite",
        salary: "$90k",
        postedTime: "today",
        logoInitial: "D",
        url: "",
        score: 88,
    },
    {
        company: "Hubflo",
        role: "Growth Marketing Associate",
        location: "NY • Hybrid",
        salary: "$70k - $120k",
        postedTime: "today",
        logoInitial: "H",
        url: "",
        score: 82,
    },
    {
        company: "Cura Labs",
        role: "Founding Engineer (Blockchain)",
        location: "Remote",
        salary: "$90k - $170k",
        postedTime: "today",
        logoInitial: "C",
        url: "",
        score: 79,
    },
    {
        company: "Enterprise Mobility",
        role: "DevOps Manager",
        location: "San Ramon",
        salary: "$100k - $120k",
        postedTime: "today",
        logoInitial: "E",
        url: "",
        score: 75,
    },
];

export default function ReportPage() {
    const [jobs, setJobs] = useState<
        Array<{
            company: string;
            role: string;
            location: string;
            salary: string;
            postedTime: string;
            logoInitial: string;
            url: string;
            score: number;
            analysis?: string;
        }>
    >([]);
    const [stats, setStats] = useState<{
        totalFound: number;
        searchTime: number;
    } | null>(null);

    useEffect(() => {
        // Try to get real results from sessionStorage
        const resultsStr = sessionStorage.getItem("searchResults");

        if (resultsStr) {
            try {
                const results: SearchResult = JSON.parse(resultsStr);

                const formattedJobs = results.top_jobs.map((scoredJob) => ({
                    company: scoredJob.job.company,
                    role: scoredJob.job.title,
                    location: scoredJob.job.location,
                    salary: scoredJob.job.salary || "Not specified",
                    postedTime: scoredJob.job.posted_time || "Recently",
                    logoInitial: scoredJob.job.logo_initial || scoredJob.job.company[0] || "?",
                    url: scoredJob.job.url,
                    score: scoredJob.overall_score,
                    analysis: scoredJob.analysis,
                }));

                setJobs(formattedJobs);
                setStats({
                    totalFound: results.total_jobs_found,
                    searchTime: results.search_time_seconds,
                });
            } catch (e) {
                console.error("Error parsing results:", e);
                setJobs(MOCK_JOBS);
            }
        } else {
            // Use mock data for demo
            setJobs(MOCK_JOBS);
        }
    }, []);

    return (
        <div className={styles.container}>
            <div className={styles.headerContainer}>
                <h1 className={styles.headerTitle}>
                    Top {jobs.length} Jobs For You
                </h1>
            </div>

            {stats && (
                <div className={styles.statsContainer}>
                    <span>Found {stats.totalFound} jobs total</span>
                    <span>•</span>
                    <span>Search completed in {stats.searchTime.toFixed(1)}s</span>
                </div>
            )}

            <div className={styles.jobList}>
                {jobs.map((job, index) => (
                    <JobCard
                        key={index}
                        company={job.company}
                        role={job.role}
                        location={job.location}
                        salary={job.salary}
                        postedTime={job.postedTime}
                        logoInitial={job.logoInitial}
                        url={job.url}
                        score={job.score}
                        analysis={job.analysis}
                    />
                ))}
            </div>

            <div className={styles.bottomFade} />
        </div>
    );
}
