import { useState } from 'react';
import { Group, Text, Stack, Badge, Alert } from '@mantine/core';
import { Dropzone, type FileWithPath } from '@mantine/dropzone';
import { IconUpload, IconX, IconFileTypePdf } from '@tabler/icons-react';
import { useDispatch } from 'react-redux';
import { addInvoice } from '../../features/data/dataSlice';

interface FileResult {
  name: string;
  status: 'processing' | 'success' | 'error';
  message: string;
}

function UploadArea() {
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<FileResult[]>([]);

  const handleFiles = async (files: FileWithPath[]) => {
    if (!files.length) return;

    setLoading(true);
    setResults([]);

    // Initialize status UI
    const initial = files.map(f => ({
      name: f.name,
      status: 'processing' as const,
      message: 'Queued'
    }));
    setResults(initial);

    try {
      // Build form data
      const formData = new FormData();
      files.forEach(file => formData.append("files", file));

      // Send to backend
      const response = await fetch("http://127.0.0.1:8000/api/extract-batch", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!data.results) {
        throw new Error("Invalid server response");
      }

      // Process each result
      data.results.forEach((res: any) => {
        if (res.status === "success") {
          dispatch(addInvoice(res.invoice));
        }

        setResults(prev => prev.map(r =>
          r.name === res.filename
            ? {
                ...r,
                status: res.status,
                message: res.status === "success" ? "Processed" : res.error || "Failed"
              }
            : r
        ));
      });

    } catch (err) {
      console.error('Upload error:', err);
      setResults(prev => prev.map(r => ({
        ...r,
        status: 'error' as const,
        message: 'Upload failed'
      })));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Stack>
      <Dropzone
        onDrop={handleFiles}
        onReject={(rejections) => {
          console.error('Files rejected:', rejections);
          alert('File rejected');
        }}
        maxSize={5 * 1024 ** 2}
        loading={loading}
      >
        <Group justify="center" gap="xl" style={{ minHeight: 120, pointerEvents: 'none' }}>
          <Dropzone.Accept><IconUpload size="3.2rem" stroke={1.5} /></Dropzone.Accept>
          <Dropzone.Reject><IconX size="3.2rem" stroke={1.5} /></Dropzone.Reject>
          <Dropzone.Idle><IconFileTypePdf size="3.2rem" stroke={1.5} /></Dropzone.Idle>
          <div>
            <Text size="xl" inline>Drag images, PDFs, or Excel files here</Text>
            <Text size="sm" c="dimmed" inline mt={7}>Attach as many files as you like</Text>
          </div>
        </Group>
      </Dropzone>

      {/* Status list */}
      {results.map((res, idx) => (
        <Alert 
          key={idx} 
          color={res.status === 'error' ? 'red' : res.status === 'success' ? 'green' : 'blue'} 
          variant="light"
        >
          <Group>
            <Badge color={res.status === 'error' ? 'red' : res.status === 'success' ? 'green' : 'blue'}>
              {res.status}
            </Badge>
            <Text>{res.name}: {res.message}</Text>
          </Group>
        </Alert>
      ))}
    </Stack>
  );
}

export default UploadArea;