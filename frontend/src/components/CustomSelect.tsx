"use client";

import { useState, useRef, useEffect } from "react";
import styles from "./CustomSelect.module.css";

interface SelectOption {
    value: string;
    label: string;
}

interface CustomSelectProps {
    options: SelectOption[];
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
}

export default function CustomSelect({ options, value, onChange, placeholder = "Select..." }: CustomSelectProps) {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    const selectedOption = options.find((opt) => opt.value === value);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleSelect = (optionValue: string) => {
        onChange(optionValue);
        setIsOpen(false);
    };

    return (
        <div className={styles.container} ref={containerRef}>
            <div
                className={`${styles.trigger} ${isOpen ? styles.active : ""}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <span className={selectedOption ? "" : styles.triggerPlaceholder}>
                    {selectedOption ? selectedOption.label : placeholder}
                </span>
                <svg
                    className={`${styles.icon} ${isOpen ? styles.active : ""}`}
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                >
                    <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
            </div>

            {isOpen && (
                <div className={styles.dropdown}>
                    {options.map((option) => (
                        <div
                            key={option.value}
                            className={`${styles.option} ${option.value === value ? styles.selected : ""}`}
                            onClick={() => handleSelect(option.value)}
                        >
                            {option.label}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
