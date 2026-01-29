import { useState } from 'react';
import { Group, Text, Stack, Badge, Alert } from '@mantine/core';
import { Dropzone, type FileWithPath } from '@mantine/dropzone';
import { IconUpload, IconX, IconFileTypePdf } from '@tabler/icons-react';
import { useDispatch } from 'react-redux';
// 🟢 FIX: Only import 'addInvoice' because it now handles EVERYTHING (Products & Customers)
import { addInvoice } from '../../features/data/dataSlice';

interface FileResult {
  name: string;
  status: 'processing' | 'success' | 'error';
  message: string;
}

function UploadArea() {
  console.log('\n========== UPLOADAREA.TSX: Component Rendering ==========');
  
  const dispatch = useDispatch();
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<FileResult[]>([]);

  const handleFiles = async (files: FileWithPath[]) => {
    console.log('\n========== UPLOADAREA.TSX: handleFiles() STARTED ==========');
    console.log('[UPLOAD] Number of files dropped:', files.length);
    
    files.forEach((file, idx) => {
      console.log(`[UPLOAD] File ${idx + 1}:`, {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: new Date(file.lastModified).toISOString()
      });
    });

    if (!files.length) {
      console.log('[UPLOAD] ⚠️ No files provided, returning');
      return;
    }

    console.log('[UPLOAD] Setting loading = true');
    setLoading(true);
    
    console.log('[UPLOAD] Clearing previous results');
    setResults([]);

    // Initialize status UI
    const initial = files.map(f => ({
      name: f.name,
      status: 'processing' as const,
      message: 'Queued'
    }));

    console.log('[UPLOAD] Setting initial results state:', initial);
    setResults(initial);

    try {
      console.log('\n[UPLOAD] Creating FormData...');
      const formData = new FormData();

      files.forEach((file, idx) => {
        console.log(`[UPLOAD] Appending file ${idx + 1} to FormData: ${file.name}`);
        formData.append("files", file);
      });

      console.log('[UPLOAD] FormData created with', files.length, 'file(s)');
      console.log('[UPLOAD] 🚀 Sending POST request to http://127.0.0.1:8000/api/extract-batch');

      const response = await fetch(
        "http://127.0.0.1:8000/api/extract-batch",
        {
          method: "POST",
          body: formData,
        }
      );

      console.log('[UPLOAD] ✅ Response received');
      console.log('[UPLOAD] Response status:', response.status);
      console.log('[UPLOAD] Response statusText:', response.statusText);
      console.log('[UPLOAD] Response ok:', response.ok);

      console.log('[UPLOAD] Parsing JSON response...');
      const data = await response.json();
      console.log('[UPLOAD] Response data:', data);
      console.log('[UPLOAD] Response data keys:', Object.keys(data));

      if (!data.results) {
        console.error('[UPLOAD] ❌ Invalid server response - missing results array');
        throw new Error("Invalid server response");
      }

      console.log('[UPLOAD] Number of results:', data.results.length);
      console.log('[UPLOAD] Processing results...');

      // Process results
      data.results.forEach((res: any, idx: number) => {
        console.log(`\n[UPLOAD] Processing result ${idx + 1}/${data.results.length}`);
        console.log(`[UPLOAD] Result ${idx + 1}:`, res);
        console.log(`[UPLOAD] - filename: ${res.filename}`);
        console.log(`[UPLOAD] - status: ${res.status}`);

        if (res.status === "success") {
          console.log(`[UPLOAD] ✅ Success for ${res.filename}`);
          console.log(`[UPLOAD] Invoice data:`, res.invoice);
          console.log(`[UPLOAD] Dispatching addInvoice action...`);
          dispatch(addInvoice(res.invoice));
          console.log(`[UPLOAD] addInvoice dispatched for ${res.filename}`);
        } else {
          console.log(`[UPLOAD] ❌ Failed for ${res.filename}`);
          console.log(`[UPLOAD] Error:`, res.error);
        }

        console.log(`[UPLOAD] Updating result state for ${res.filename}...`);
        setResults(prev => {
          const updated = prev.map(r =>
            r.name === res.filename
              ? {
                  ...r,
                  status: res.status,
                  message:
                    res.status === "success"
                      ? "Processed"
                      : res.error || "Failed"
                }
              : r
          );
          console.log(`[UPLOAD] Updated results state:`, updated);
          return updated;
        });
      });

      console.log('[UPLOAD] ✅ All results processed successfully');

    } catch (err) {
      console.error('\n[UPLOAD] ❌ ERROR in handleFiles:', err);
      console.error('[UPLOAD] Error type:', typeof err);
      console.error('[UPLOAD] Error message:', err instanceof Error ? err.message : String(err));
      console.error('[UPLOAD] Error stack:', err instanceof Error ? err.stack : 'N/A');

      console.log('[UPLOAD] Setting all results to error state...');
      setResults(prev => {
        const errorResults = prev.map(r => ({
          ...r,
          status: 'error' as const,
          message: 'Upload failed'
        }));
        console.log('[UPLOAD] Error results state:', errorResults);
        return errorResults;
      });

    } finally {
      console.log('\n[UPLOAD] Finally block - setting loading = false');
      setLoading(false);
      console.log('========== UPLOADAREA.TSX: handleFiles() COMPLETED ==========\n');
    }
  };

  console.log('[UPLOAD] Current state:');
  console.log('  - loading:', loading);
  console.log('  - results count:', results.length);
  console.log('  - results:', results);

  return (
    <Stack>
      <Dropzone
        onDrop={(files) => {
          console.log('[UPLOAD] Dropzone onDrop triggered');
          handleFiles(files);
        }}
        onReject={(rejections) => {
          console.error('[UPLOAD] Dropzone onReject triggered');
          console.error('[UPLOAD] Rejected files:', rejections);
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

      {/* Status List */}
      {results.map((res, idx) => {
        console.log(`[UPLOAD] Rendering result ${idx + 1}:`, res);
        return (
          <Alert key={idx} color={res.status === 'error' ? 'red' : res.status === 'success' ? 'green' : 'blue'} variant="light">
            <Group>
              <Badge color={res.status === 'error' ? 'red' : res.status === 'success' ? 'green' : 'blue'}>
                {res.status}
              </Badge>
              <Text>{res.name}: {res.message}</Text>
            </Group>
          </Alert>
        );
      })}
    </Stack>
  );
}

console.log('[UPLOAD] UploadArea component defined');

export default UploadArea;