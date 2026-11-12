export const vertex = `
attribute vec2 aPosition;
varying vec2 vUv;
void main() {
  vUv = vec2(aPosition.x * .5 + .5, .5 - aPosition.y * .5);
  gl_Position = vec4(aPosition, 0., 1.);
}`;

// Each timing texture records when the pen reaches a point along a stroke.
// Advancing progress extends individual marks; no photograph is sampled here.
export const fragment = `
precision mediump float;
varying vec2 vUv;
uniform sampler2D uInk0;
uniform sampler2D uTime0;
uniform sampler2D uInk1;
uniform sampler2D uTime1;
uniform sampler2D uInk2;
uniform sampler2D uTime2;
uniform vec2 uScale;
uniform vec2 uOffset;
uniform float uResolve;

vec3 addStrokes(vec3 ground, sampler2D inkTexture, sampler2D timeTexture, vec2 uv) {
  vec4 ink = texture2D(inkTexture, uv);
  float arrival = texture2D(timeTexture, uv).r * 1.1 - .1;
  float drawn = uResolve >= .999 ? 1. : smoothstep(arrival - .006, arrival + .006, uResolve);
  float luminance = dot(ink.rgb, vec3(.2126, .7152, .0722));
  float saturation = .3 + .7 * smoothstep(.05, .92, uResolve);
  vec3 color = mix(vec3(luminance), ink.rgb, saturation);
  return mix(ground, color, ink.a * drawn);
}
void main() {
  vec2 uv = vUv * uScale + uOffset;
  vec3 result = vec3(243. / 255., 240. / 255., 231. / 255.);
  result = addStrokes(result, uInk0, uTime0, uv);
  result = addStrokes(result, uInk1, uTime1, uv);
  result = addStrokes(result, uInk2, uTime2, uv);
  gl_FragColor = vec4(result, 1.);
}`;
