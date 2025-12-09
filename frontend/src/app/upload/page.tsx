import UploadWidget from "../../components/UploadWidget";
import styles from "../page.module.css"; // Reuse main styles for convenience if needed, or inline for layout

export default function Upload() {
    return (
        <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            height: '100%',
            width: '100%',
            position: 'relative',
            zIndex: 10
        }}>
            <UploadWidget />
        </div>
    );
}
