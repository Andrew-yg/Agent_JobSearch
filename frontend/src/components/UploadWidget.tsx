"use client";

import { useState, useRef, ChangeEvent, DragEvent } from "react";
import { useRouter } from "next/navigation";
import CustomSelect from "./CustomSelect";
import styles from "./UploadWidget.module.css";

interface UploadedFile {
    id: string;
    name: string;
    size: number;
    status: "uploading" | "success" | "error";
    progress: number;
    file?: File; // Keep reference to actual file
}

interface JobDetails {
    keywords: string;
    location: string;
    experience: string;
    postedTime: string;
    jobType: string;
}

interface ValidationErrors {
    keywords?: string;
    location?: string;
}

type Step = "upload" | "details";

const API_BASE = "http://localhost:8000/api";

export default function UploadWidget() {
    const router = useRouter();
    const [step, setStep] = useState<Step>("upload");
    const [files, setFiles] = useState<UploadedFile[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [resumeId, setResumeId] = useState<string | null>(null);
    const [errors, setErrors] = useState<ValidationErrors>({});
    const [jobDetails, setJobDetails] = useState<JobDetails>({
        keywords: "",
        location: "",
        experience: "internship",
        postedTime: "24h",
        jobType: "remote",
    });

    const fileInputRef = useRef<HTMLInputElement>(null);

    const validatePDF = (file: File): boolean => {
        if (!file.name.toLowerCase().endsWith(".pdf")) {
            alert("Only PDF files are allowed. Please upload your resume as a PDF.");
            return false;
        }
        if (file.size > 10 * 1024 * 1024) {
            alert("File size exceeds 10MB limit.");
            return false;
        }
        return true;
    };

    const uploadToBackend = async (file: File): Promise<string | null> => {
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || "Upload failed");
            }

            const data = await response.json();
            return data.resume_id;
        } catch (error) {
            console.error("Upload error:", error);
            return null;
        }
    };

    const handleFileUpload = async (newFiles: File[]) => {
        // Filter to only PDF files
        const pdfFiles = newFiles.filter(validatePDF);
        if (pdfFiles.length === 0) return;

        // Only allow one resume at a time
        const file = pdfFiles[0];

        const newUploadedFile: UploadedFile = {
            id: Math.random().toString(36).substring(7),
            name: file.name,
            size: file.size,
            status: "uploading",
            progress: 0,
            file: file,
        };

        setFiles([newUploadedFile]);

        // Simulate progress while uploading
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            if (progress >= 90) {
                clearInterval(interval);
            }
            setFiles((prev) =>
                prev.map((f) =>
                    f.id === newUploadedFile.id ? { ...f, progress } : f
                )
            );
        }, 100);

        // Actually upload to backend
        const uploadedResumeId = await uploadToBackend(file);
        clearInterval(interval);

        if (uploadedResumeId) {
            setResumeId(uploadedResumeId);
            setFiles((prev) =>
                prev.map((f) =>
                    f.id === newUploadedFile.id
                        ? { ...f, status: "success", progress: 100 }
                        : f
                )
            );
        } else {
            setFiles((prev) =>
                prev.map((f) =>
                    f.id === newUploadedFile.id
                        ? { ...f, status: "error", progress: 0 }
                        : f
                )
            );
        }
    };

    const handleDragEnter = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    };

    const handleDrop = (e: DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileUpload(Array.from(e.dataTransfer.files));
        }
    };

    const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFileUpload(Array.from(e.target.files));
        }
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    const removeFile = (id: string) => {
        setFiles((prev) => prev.filter((f) => f.id !== id));
        setResumeId(null);
    };

    const formatSize = (bytes: number) => {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
    };

    const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setJobDetails((prev) => ({ ...prev, [name]: value }));
        // Clear error when user types
        if (errors[name as keyof ValidationErrors]) {
            setErrors((prev) => ({ ...prev, [name]: undefined }));
        }
    };

    const validateForm = (): boolean => {
        const newErrors: ValidationErrors = {};

        if (!jobDetails.keywords.trim()) {
            newErrors.keywords = "Job keywords are required";
        }
        if (!jobDetails.location.trim()) {
            newErrors.location = "Location is required";
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleNextStep = async () => {
        if (step === "upload") {
            if (!resumeId) {
                alert("Please upload your resume first");
                return;
            }
            setStep("details");
        } else {
            // Validate form before submit
            if (!validateForm()) {
                return;
            }

            // Store search params in sessionStorage for agent page
            sessionStorage.setItem(
                "searchParams",
                JSON.stringify({
                    resumeId,
                    ...jobDetails,
                })
            );

            // Navigate to agent page
            router.push("/agent-react");
        }
    };

    const handleCancel = () => {
        if (step === "details") {
            setStep("upload");
        } else {
            setFiles([]);
            setResumeId(null);
        }
    };

    // Header Content
    const title = step === "upload" ? "Upload Resume" : "Job Details";
    const subtitle =
        step === "upload"
            ? "Upload your resume (PDF only) to get started."
            : "Tell us what kind of jobs you're looking for.";

    const isUploadComplete = files.length > 0 && files[0].status === "success";

    return (
        <div className={styles.widgetContainer}>
            <header className={styles.header}>
                <div>
                    <h2 className={styles.title}>{title}</h2>
                    <p className={styles.subtitle}>{subtitle}</p>
                </div>
                <button className={styles.closeButton}>
                    <svg
                        width="24"
                        height="24"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </header>

            {/* Step 1: Upload View */}
            {step === "upload" && (
                <>
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        accept=".pdf"
                        style={{ display: "none" }}
                    />

                    <div
                        className={`${styles.dropZone} ${isDragging ? styles.dropZoneActive : ""}`}
                        onDragEnter={handleDragEnter}
                        onDragOver={handleDragEnter}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        onClick={() => fileInputRef.current?.click()}
                    >
                        <div className={styles.dropZoneIcon}>
                            <svg
                                width="48"
                                height="48"
                                viewBox="0 0 24 24"
                                fill="none"
                                xmlns="http://www.w3.org/2000/svg"
                            >
                                <path
                                    d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z"
                                    stroke="#4B5563"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                                <path
                                    d="M14 2V8H20"
                                    stroke="#4B5563"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                                <path
                                    d="M16 13H8"
                                    stroke="#4B5563"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                                <path
                                    d="M16 17H8"
                                    stroke="#4B5563"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                                <path
                                    d="M10 9H8"
                                    stroke="#4B5563"
                                    strokeWidth="2"
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                />
                            </svg>
                        </div>
                        <div className={styles.dropText}>
                            Drag and drop your resume
                        </div>
                        <div className={styles.dropSubtext}>
                            PDF format only, up to 10MB
                        </div>
                        <button
                            className={styles.selectButton}
                            onClick={(e) => {
                                e.stopPropagation();
                                fileInputRef.current?.click();
                            }}
                        >
                            Select PDF
                        </button>
                    </div>

                    <div className={styles.fileList}>
                        {files.map((file) => (
                            <div key={file.id} className={styles.fileItem}>
                                <div className={styles.fileIcon}>
                                    <svg
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                        <polyline points="14 2 14 8 20 8"></polyline>
                                        <line x1="16" y1="13" x2="8" y2="13"></line>
                                        <line x1="16" y1="17" x2="8" y2="17"></line>
                                        <line x1="10" y1="9" x2="8" y2="9"></line>
                                    </svg>
                                </div>
                                <div className={styles.fileInfo}>
                                    <span className={styles.fileName}>
                                        {file.name}
                                    </span>
                                    <div className={styles.fileStatus}>
                                        {formatSize(file.size)} •{" "}
                                        {file.status === "uploading"
                                            ? `${file.progress}%`
                                            : file.status === "success"
                                                ? "Uploaded Successfully"
                                                : "Upload Failed"}
                                    </div>
                                    <div className={styles.progressBar}>
                                        <div
                                            className={`${styles.progressFill} ${file.status === "uploading"
                                                    ? styles.uploading
                                                    : file.status === "error"
                                                        ? styles.error
                                                        : ""
                                                }`}
                                            style={{ width: `${file.progress}%` }}
                                        />
                                    </div>
                                </div>
                                <button
                                    className={styles.deleteButton}
                                    onClick={() => removeFile(file.id)}
                                >
                                    <svg
                                        width="16"
                                        height="16"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                    >
                                        <polyline points="3 6 5 6 21 6"></polyline>
                                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                    </svg>
                                </button>
                            </div>
                        ))}
                    </div>
                </>
            )}

            {/* Step 2: Form View */}
            {step === "details" && (
                <div className={styles.formContainer}>
                    <div className={styles.formGroup}>
                        <label className={styles.label}>
                            Job Keywords <span className={styles.required}>*</span>
                        </label>
                        <input
                            type="text"
                            name="keywords"
                            placeholder="e.g. React, Node.js, Full Stack"
                            className={`${styles.input} ${errors.keywords ? styles.inputError : ""}`}
                            value={jobDetails.keywords}
                            onChange={handleInputChange}
                        />
                        {errors.keywords && (
                            <span className={styles.errorText}>{errors.keywords}</span>
                        )}
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.label}>
                            Location <span className={styles.required}>*</span>
                        </label>
                        <input
                            type="text"
                            name="location"
                            placeholder="e.g. New York, San Francisco, Remote"
                            className={`${styles.input} ${errors.location ? styles.inputError : ""}`}
                            value={jobDetails.location}
                            onChange={handleInputChange}
                        />
                        {errors.location && (
                            <span className={styles.errorText}>{errors.location}</span>
                        )}
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.label}>Experience Level</label>
                        <CustomSelect
                            options={[
                                { value: "internship", label: "Internship" },
                                { value: "entry", label: "Entry Level" },
                                { value: "mid", label: "Mid Level" },
                                { value: "senior", label: "Senior Level" },
                            ]}
                            value={jobDetails.experience}
                            onChange={(val) =>
                                setJobDetails((prev) => ({
                                    ...prev,
                                    experience: val,
                                }))
                            }
                            placeholder="Select Level"
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.label}>Posted Time</label>
                        <CustomSelect
                            options={[
                                { value: "24h", label: "Last 24 hours" },
                                { value: "week", label: "Last Week" },
                                { value: "month", label: "Last Month" },
                            ]}
                            value={jobDetails.postedTime}
                            onChange={(val) =>
                                setJobDetails((prev) => ({
                                    ...prev,
                                    postedTime: val,
                                }))
                            }
                            placeholder="Select Time"
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label className={styles.label}>Job Type</label>
                        <CustomSelect
                            options={[
                                { value: "remote", label: "Remote" },
                                { value: "onsite", label: "Onsite" },
                                { value: "hybrid", label: "Hybrid" },
                            ]}
                            value={jobDetails.jobType}
                            onChange={(val) =>
                                setJobDetails((prev) => ({
                                    ...prev,
                                    jobType: val,
                                }))
                            }
                            placeholder="Select Type"
                        />
                    </div>
                </div>
            )}

            <div className={styles.footer}>
                <button className={styles.cancelButton} onClick={handleCancel}>
                    Cancel
                </button>
                <button
                    className={styles.attachButton}
                    onClick={handleNextStep}
                    disabled={
                        (step === "upload" && !isUploadComplete) || isSubmitting
                    }
                >
                    {isSubmitting
                        ? "Processing..."
                        : step === "upload"
                            ? "Continue"
                            : "Start Search"}
                </button>
            </div>
        </div>
    );
}
