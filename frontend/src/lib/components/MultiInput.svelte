<script lang="ts">
  import { createEventDispatcher } from "svelte";

  export let fieldName: string;
  export let label: string;
  export let required: boolean = false;
  export let value: string = "";

  const dispatch = createEventDispatcher();

  let activeTab: "text" | "file" | "url" = "text";
  let textValue = value;
  let urlValue = "";
  let selectedFile: File | null = null;
  let fileError: string | null = null;
  let isLoading = false;
  let dragOver = false;

  // Update textValue when value prop changes
  $: if (value && activeTab === "text") {
    textValue = value;
  }

  function handleTabChange(tab: "text" | "file" | "url") {
    // Warn if switching tabs with existing content
    if (
      (activeTab === "text" && textValue) ||
      (activeTab === "file" && selectedFile) ||
      (activeTab === "url" && urlValue)
    ) {
      if (!confirm("Switching tabs will discard your current input. Continue?")) {
        return;
      }
    }

    activeTab = tab;
    selectedFile = null;
    fileError = null;
    urlValue = "";
    textValue = "";
    dispatch("change", { content: null, metadata: null });
  }

  function handleTextChange() {
    dispatch("change", {
      content: textValue,
      metadata: { type: "text" },
    });
  }

  function handleUrlChange() {
    const url = urlValue.trim();
    if (url) {
      // Basic URL validation
      try {
        new URL(url);
        dispatch("change", {
          content: url,
          metadata: { type: "url", url },
        });
      } catch {
        // Invalid URL, but let backend handle validation
        dispatch("change", {
          content: url,
          metadata: { type: "url", url },
        });
      }
    } else {
      dispatch("change", { content: null, metadata: null });
    }
  }

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      processFile(target.files[0]);
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragOver = true;
  }

  function handleDragLeave() {
    dragOver = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragOver = false;

    if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
      processFile(event.dataTransfer.files[0]);
    }
  }

  function processFile(file: File) {
    fileError = null;

    // Validate file type
    const allowedTypes = [
      "application/pdf",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    const allowedExtensions = [".pdf", ".doc", ".docx"];

    const fileExtension = "." + file.name.split(".").pop()?.toLowerCase();
    const isValidType =
      allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension);

    if (!isValidType) {
      fileError = "Please upload a PDF or Word document (.pdf, .doc, .docx)";
      return;
    }

    // Validate file size (10MB)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      fileError = "File size must be under 10MB";
      return;
    }

    if (file.size === 0) {
      fileError = "File is empty";
      return;
    }

    selectedFile = file;
    dispatch("change", {
      content: file,
      metadata: {
        type: "file",
        filename: file.name,
        fileSize: file.size,
        fileType: file.type,
      },
    });
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1024 / 1024).toFixed(1) + " MB";
  }

  function removeFile() {
    selectedFile = null;
    fileError = null;
    dispatch("change", { content: null, metadata: null });
  }
</script>

<div class="space-y-3">
  <label class="block text-sm font-semibold text-gray-300 mb-3">
    {label}
    {#if required}
      <span class="text-red-400">*</span>
    {/if}
  </label>

  <!-- Tab Navigation -->
  <div class="flex gap-2 border-b border-slate-700">
    <button
      type="button"
      class="px-4 py-2 text-sm font-medium transition-colors {activeTab === 'text'
        ? 'text-blue-400 border-b-2 border-blue-400'
        : 'text-gray-400 hover:text-gray-300'}"
      on:click={() => handleTabChange("text")}
    >
      Plain Text
    </button>
    <button
      type="button"
      class="px-4 py-2 text-sm font-medium transition-colors {activeTab === 'file'
        ? 'text-blue-400 border-b-2 border-blue-400'
        : 'text-gray-400 hover:text-gray-300'}"
      on:click={() => handleTabChange("file")}
    >
      Upload File
    </button>
    <button
      type="button"
      class="px-4 py-2 text-sm font-medium transition-colors {activeTab === 'url'
        ? 'text-blue-400 border-b-2 border-blue-400'
        : 'text-gray-400 hover:text-gray-300'}"
      on:click={() => handleTabChange("url")}
    >
      From URL
    </button>
  </div>

  <!-- Text Tab -->
  {#if activeTab === "text"}
    <textarea
      id={fieldName}
      bind:value={textValue}
      on:input={handleTextChange}
      rows="6"
      class="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-200 placeholder-gray-500 transition-all duration-200"
      placeholder="Enter {label.toLowerCase()}..."
      {required}
    ></textarea>
  {/if}

  <!-- File Tab -->
  {#if activeTab === "file"}
    <div
      class="border-2 border-dashed rounded-xl p-8 text-center transition-colors {dragOver
        ? 'border-blue-500 bg-blue-500/10'
        : 'border-slate-600 bg-slate-900/30'}"
      on:dragover={handleDragOver}
      on:dragleave={handleDragLeave}
      on:drop={handleDrop}
    >
      {#if selectedFile}
        <div class="space-y-3">
          <div class="flex items-center justify-center gap-3">
            <svg
              class="w-8 h-8 text-green-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              ></path>
            </svg>
            <div class="text-left">
              <p class="text-gray-200 font-medium">{selectedFile.name}</p>
              <p class="text-gray-400 text-sm">{formatFileSize(selectedFile.size)}</p>
            </div>
            <button
              type="button"
              on:click={removeFile}
              class="ml-auto text-red-400 hover:text-red-300 transition-colors"
              title="Remove file"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M6 18L18 6M6 6l12 12"
                ></path>
              </svg>
            </button>
          </div>
        </div>
      {:else}
        <div class="space-y-4">
          <svg
            class="w-12 h-12 text-gray-400 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            ></path>
          </svg>
          <div>
            <p class="text-gray-300 font-medium">Drag and drop your file here</p>
            <p class="text-gray-500 text-sm mt-1">or click to browse</p>
          </div>
          <label
            for="file-{fieldName}"
            class="inline-block px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg cursor-pointer transition-colors"
          >
            Select File
          </label>
          <input
            id="file-{fieldName}"
            type="file"
            accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            class="hidden"
            on:change={handleFileSelect}
          />
          <p class="text-gray-500 text-xs">PDF, DOC, or DOCX (max 10MB)</p>
        </div>
      {/if}

      {#if fileError}
        <div
          class="mt-4 p-3 bg-red-900/30 border border-red-700/50 text-red-300 rounded-lg text-sm"
        >
          {fileError}
        </div>
      {/if}
    </div>
  {/if}

  <!-- URL Tab -->
  {#if activeTab === "url"}
    <div class="space-y-3">
      <input
        type="url"
        bind:value={urlValue}
        on:input={handleUrlChange}
        class="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-200 placeholder-gray-500 transition-all duration-200"
        placeholder="https://example.com/job-posting"
        {required}
      />
      <p class="text-gray-500 text-xs">
        Enter a job posting URL. We'll extract the content automatically.
      </p>
      {#if urlValue && urlValue.includes("linkedin.com")}
        <div
          class="p-3 bg-yellow-900/30 border border-yellow-700/50 text-yellow-300 rounded-lg text-sm"
        >
          Note: LinkedIn profiles cannot be automatically imported. Please use the Plain Text tab
          instead.
        </div>
      {/if}
    </div>
  {/if}
</div>
