-- Set up storage RLS policies for interview-files bucket
-- Allow service role to perform all operations (upload, read, delete)

-- Enable RLS on storage.objects if not already enabled
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if it exists
DROP POLICY IF EXISTS "Allow service role full access to interview-files" ON storage.objects;

-- Create policy to allow service role full access to interview-files bucket
CREATE POLICY "Allow service role full access to interview-files"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'interview-files')
WITH CHECK (bucket_id = 'interview-files');

-- Also allow authenticated users to read files (if needed in future)
-- For now, we'll keep it service_role only for security
-- Uncomment below if you need authenticated users to read files:
-- DROP POLICY IF EXISTS "Allow authenticated users to read interview-files" ON storage.objects;
-- CREATE POLICY "Allow authenticated users to read interview-files"
-- ON storage.objects
-- FOR SELECT
-- TO authenticated
-- USING (bucket_id = 'interview-files');
