import { vertex, fragment } from './shaders.js';
import { bufferSize } from './math.js';
import { coverCrop } from './composition.js';

const assetRoot = new URL('../assets/', import.meta.url);

function compile(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const message = gl.getShaderInfoLog(shader);
    gl.deleteShader(shader);
    throw new Error(`Landscape shader: ${message}`);
  }
  return shader;
}

async function loadImages(variant, signal) {
  const files = ['photo.webp', 'drawing.webp', 'control.png'];
  const results = await Promise.allSettled(files.map(async (file) => {
    const response = await fetch(new URL(`${variant}/${file}`, assetRoot), { signal });
    if (!response.ok) throw new Error(`Landscape image unavailable (${response.status})`);
    const bitmap = await createImageBitmap(await response.blob(), { premultiplyAlpha: 'none' });
    if (signal.aborted) { bitmap.close(); throw new DOMException('Aborted', 'AbortError'); }
    return bitmap;
  }));
  if (signal.aborted || results.some((result) => result.status === 'rejected')) {
    for (const result of results) if (result.status === 'fulfilled') result.value.close();
    throw new Error('Landscape images could not be decoded');
  }
  return results.map((result) => result.value);
}

export class LandscapeRenderer {
  constructor(canvas, onFailure) {
    this.canvas = canvas;
    this.gl = canvas.getContext('webgl', { alpha: false, antialias: false, depth: false, stencil: false, preserveDrawingBuffer: false });
    if (!this.gl) throw new Error('WebGL unavailable');
    this.textures = [];
    this.cache = new Map();
    this.disposed = false;
    this.generation = 0;
    this.onLoss = (event) => { event.preventDefault(); onFailure(new Error('Landscape context lost')); };
    canvas.addEventListener('webglcontextlost', this.onLoss);
    const gl = this.gl;
    let vs, fs;
    try {
      vs = compile(gl, gl.VERTEX_SHADER, vertex);
      fs = compile(gl, gl.FRAGMENT_SHADER, fragment);
      this.program = gl.createProgram();
      gl.attachShader(this.program, vs); gl.attachShader(this.program, fs);
      gl.linkProgram(this.program);
      if (!gl.getProgramParameter(this.program, gl.LINK_STATUS)) throw new Error('Landscape shader link failed');
      gl.useProgram(this.program);
      this.buffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, this.buffer);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);
      const position = gl.getAttribLocation(this.program, 'aPosition');
      gl.enableVertexAttribArray(position);
      gl.vertexAttribPointer(position, 2, gl.FLOAT, false, 0, 0);
      this.uniforms = Object.fromEntries(['Photo', 'Drawing', 'Control', 'Scale', 'Offset', 'Resolve', 'Velocity'].map((key) => [key, gl.getUniformLocation(this.program, `u${key}`)]));
      ['Photo', 'Drawing', 'Control'].forEach((key, i) => gl.uniform1i(this.uniforms[key], i));
      this.maxTexture = gl.getParameter(gl.MAX_TEXTURE_SIZE);
      const viewport = gl.getParameter(gl.MAX_VIEWPORT_DIMS);
      this.maxAxis = Math.min(gl.getParameter(gl.MAX_RENDERBUFFER_SIZE), ...viewport);
    } catch (error) { this.dispose(); throw error; }
    finally { if (vs) gl.deleteShader(vs); if (fs) gl.deleteShader(fs); }
  }

  async setVariant(variant, meta, commit) {
    const generation = ++this.generation;
    this.pending?.abort();
    const controller = new AbortController();
    this.pending = controller;
    const timeout = setTimeout(() => controller.abort(), 12_000);
    let images = [], textures = [], ownsImages = false;
    try {
      const cached = this.cache.get(variant);
      images = cached ? cached.images : await loadImages(variant, controller.signal);
      ownsImages = !cached;
      if (this.disposed || generation !== this.generation) return false;
      const gl = this.gl;
      for (const image of images) {
        if (image.width > this.maxTexture || image.height > this.maxTexture) throw new Error('Landscape exceeds texture limit');
        const texture = gl.createTexture();
        if (!texture) throw new Error('Landscape texture allocation failed');
        textures.push(texture);
        gl.bindTexture(gl.TEXTURE_2D, texture);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, image);
        if (gl.getError() !== gl.NO_ERROR) throw new Error('Landscape texture upload failed');
      }
      // Decode the HTML endpoint before changing either visible layer.
      const photo = cached?.photo || new Image();
      photo.className = 'managed-photo'; photo.id = 'managed-photo';
      photo.alt = ''; photo.setAttribute('aria-hidden', 'true');
      if (!cached) photo.src = new URL(`${variant}/photo.webp`, assetRoot).href;
      await Promise.race([
        photo.decode(),
        new Promise((_, reject) => {
          if (controller.signal.aborted) reject(new Error('Landscape load cancelled'));
          else controller.signal.addEventListener('abort', () => reject(new Error('Landscape load cancelled')), { once: true });
        }),
      ]);
      if (this.disposed || generation !== this.generation) return false;
      const oldTextures = this.textures;
      this.textures = textures; textures = [];
      this.meta = meta;
      this.variant = variant;
      // Only the two known variants can enter the cache. Keep decoded images
      // for cheap orientation returns; only the active variant owns GPU textures.
      this.cache.set(variant, { images, photo });
      ownsImages = false;
      try { commit(photo); }
      finally { oldTextures.forEach((texture) => gl.deleteTexture(texture)); }
      return true;
    } catch (error) {
      if (!this.disposed && generation === this.generation) throw error;
      return false;
    } finally {
      clearTimeout(timeout);
      if (ownsImages) images.forEach((image) => image.close());
      textures.forEach((texture) => this.gl.deleteTexture(texture));
      if (this.pending === controller) this.pending = null;
    }
  }

  resize(width, height) {
    if (this.disposed || !this.meta) return;
    const gl = this.gl;
    const [w, h] = bufferSize(width, height, window.devicePixelRatio || 1, 2_500_000, this.maxAxis);
    if (this.canvas.width !== w || this.canvas.height !== h) { this.canvas.width = w; this.canvas.height = h; }
    gl.viewport(0, 0, w, h);
    this.crop = coverCrop(width, height, this.meta.width, this.meta.height, this.meta.focal, this.meta.subject, this.meta.peak);
    this.canvas.parentElement.style.setProperty('--position-x', `${this.crop.position[0] * 100}%`);
    this.canvas.parentElement.style.setProperty('--position-y', `${this.crop.position[1] * 100}%`);
  }

  draw(resolve, velocity = 0) {
    if (this.disposed || !this.crop || this.textures.length !== 3) return;
    const gl = this.gl;
    gl.useProgram(this.program);
    this.textures.forEach((texture, i) => { gl.activeTexture(gl.TEXTURE0 + i); gl.bindTexture(gl.TEXTURE_2D, texture); });
    gl.uniform2fv(this.uniforms.Scale, this.crop.scale);
    gl.uniform2fv(this.uniforms.Offset, this.crop.offset);
    gl.uniform1f(this.uniforms.Resolve, resolve);
    gl.uniform1f(this.uniforms.Velocity, Math.max(-1, Math.min(1, velocity)));
    gl.drawArrays(gl.TRIANGLES, 0, 6);
  }

  dispose() {
    if (this.disposed) return;
    this.disposed = true; this.generation++;
    this.pending?.abort();
    this.canvas.removeEventListener('webglcontextlost', this.onLoss);
    const gl = this.gl;
    this.textures.forEach((texture) => gl.deleteTexture(texture)); this.textures = [];
    for (const entry of this.cache.values()) entry.images.forEach((image) => image.close());
    this.cache.clear();
    if (this.buffer) gl.deleteBuffer(this.buffer);
    if (this.program) gl.deleteProgram(this.program);
  }
}
