import styles from "./page.module.css";
import { MouseEvent } from "react";
import Link from "next/link";

export default function Home() {
  return (
    <>
      {/* Hero Content */}
      <h1 className={styles.heading}>
        Building blocks for data security and compliance
      </h1>

      <p className={styles.paragraph}>
        Evervault provides developers with world-class infrastructure to solve complex data security and compliance problems in days, not months.
      </p>

      <div className={styles.buttonsContainer}>
        <Link href="/upload" className={styles.primaryButton}>
          <span className={styles.primaryButtonText}>Get Started without Login</span>
        </Link>
      </div>
    </>
  );
}
