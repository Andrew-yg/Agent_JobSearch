"use client";

import { MouseEvent, ReactNode } from "react";
import Link from "next/link";
import styles from "../app/page.module.css";

interface BackgroundLayoutProps {
    children: ReactNode;
}

export default function BackgroundLayout({ children }: BackgroundLayoutProps) {
    const handleMouseMove = (e: MouseEvent<HTMLElement>) => {
        const x = e.clientX;
        const y = e.clientY;

        // We update CSS variables on the current target (main)
        // The background gradient wrapper (child) will use these variables.
        // We adjust X/Y by 20px because the wrapper is offset by 20px, 
        // so we want the center of the radial gradient to match the cursor position relative to the wrapper.
        e.currentTarget.style.setProperty('--mouse-x', `${x - 20}px`);
        e.currentTarget.style.setProperty('--mouse-y', `${y - 20}px`);
    };

    return (
        <main className={styles.main} onMouseMove={handleMouseMove}>
            <div className={styles.heroGradientWrapper} />

            {/* Header */}
            <header className={styles.header}>
                <div className={styles.logoContainer}>
                    {/* Simple Stack Icon SVG Placeholder */}
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                        <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                    Agent_JobSearch
                </div>

                <nav className={styles.navContainer}>
                    <Link href="/" className={styles.navLink}>Home</Link>
                    <Link href="/upload" className={styles.navLink}>Upload</Link>
                    <Link href="#" className={styles.navLink}>Agent ReAct</Link>
                    <Link href="#" className={styles.navLink}>Report</Link>
                </nav>

                {/* Placeholder for alignment or empty since auth is removed */}
                <div style={{ width: '100px' }}></div>
            </header>

            {/* Page Content */}
            {children}
        </main>
    );
}
