# Supabase Storage Setup Guide

## Issue: RLS Policy Error on File Upload

When uploading files to Supabase Storage, you may encounter:
```
"new row violates row-level security policy"
```

This happens because Supabase Storage requires RLS policies to be set up, even when using the service role key.

## Solution: Set Up Storage Policies via Dashboard

Since we can't create storage policies via SQL migrations (permission restrictions), you need to set them up through the Supabase Dashboard:

### Step 1: Navigate to Storage Policies

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Storage** → **Policies**
4. Select the `interview-files` bucket

### Step 2: Create Upload Policy

Create a policy to allow service role to upload files:

**Policy Name:** `Allow service role uploads`

**Policy Definition:**
```sql
CREATE POLICY "Allow service role uploads"
ON storage.objects
FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'interview-files');
```

**Steps in Dashboard:**
1. Click **"New Policy"**
2. Select **"For full customization"**
3. Policy name: `Allow service role uploads`
4. Allowed operation: **INSERT**
5. Target roles: **service_role**
6. WITH CHECK expression: `bucket_id = 'interview-files'`

### Step 3: Create Read Policy (Optional but Recommended)

Create a policy to allow service role to read files:

**Policy Name:** `Allow service role reads`

**Policy Definition:**
```sql
CREATE POLICY "Allow service role reads"
ON storage.objects
FOR SELECT
TO service_role
USING (bucket_id = 'interview-files');
```

**Steps in Dashboard:**
1. Click **"New Policy"**
2. Select **"For full customization"**
3. Policy name: `Allow service role reads`
4. Allowed operation: **SELECT**
5. Target roles: **service_role**
6. USING expression: `bucket_id = 'interview-files'`

### Step 4: Create Delete Policy (Optional)

If you need to delete files:

**Policy Name:** `Allow service role deletes`

**Policy Definition:**
```sql
CREATE POLICY "Allow service role deletes"
ON storage.objects
FOR DELETE
TO service_role
USING (bucket_id = 'interview-files');
```

## Alternative: Use Supabase MCP

If you have access to Supabase MCP tools, you can also try setting up policies programmatically, though the SQL approach may have permission restrictions.

## Verification

After setting up the policies, test file upload:

```bash
# Test via API
curl -X POST http://localhost:8000/api/interviews \
  -F "job_description_text=Test job" \
  -F "job_description_type=text" \
  -F "resume_text=@/path/to/test.pdf" \
  -F "resume_type=file" \
  -F "status=pending"
```

## Notes

- The service role key should bypass RLS, but Supabase Storage still requires explicit policies
- These policies ensure that only the service role can upload/read files in the `interview-files` bucket
- Never expose the service role key in client-side code
