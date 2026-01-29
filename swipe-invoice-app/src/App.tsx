import { MantineProvider, Container, Title, Stack } from '@mantine/core';
import UploadArea from './components/upload/UploadArea';
import Dashboard from './components/Dashboard';
import '@mantine/core/styles.css';
import '@mantine/dropzone/styles.css';
import 'mantine-react-table/styles.css'; // Don't forget table styles!

function App() {
  return (
    <MantineProvider>
      <Container size="xl" py="xl">
        <Stack gap="lg">
          <Title order={1} ta="center">Swipe Automated Extraction</Title>
          
          {/* 1. Drag & Drop Area */}
          <UploadArea />
          
          {/* 2. Results Dashboard */}
          <Dashboard />
        </Stack>
      </Container>
    </MantineProvider>
  );
}

export default App;