import styles from "./page.module.css";
import { MouseEvent } from "react";
import Link from "next/link";

export default function Home() {
  return (
    <>
      {/* Hero Content */}
      <h1 className={styles.heading}>
        AI agent for intelligent job discovery and perfect matches
      </h1>

      <p className={styles.paragraph}>
        Let AI search LinkedIn 24/7, match jobs to your resume, and deliver your top 10 opportunities—while you focus on interview prep.
      </p>

      <div className={styles.buttonsContainer}>
        <Link href="/upload" className={styles.primaryButton}>
          <span className={styles.primaryButtonText}>Get Started without Login</span>
        </Link>
      </div>
    </>
  );
}
