import fs from 'node:fs/promises';
const root='/Users/trvzera/Desktop/BOOSTio';
const out=root+'/materiais/exportacoes/apresentacao/2026-11-10-v2';
const skill='/Users/trvzera/.codex/plugins/cache/openai-primary-runtime/presentations/26.1105.12137/skills/presentations';
const {finalizePresentation}=await import('file://'+skill+'/container_tools/artifact_tool_utils.mjs');
const source='/Users/trvzera/Library/Application Support/Codex/artifact-sessions/exports/latest/cc08cd1e61eefaab0869733f9cf0e36d2340f06958207694d517ff44ef1fe163/BOOSTio-Pitch-3A2-v2-com-roteiro.pptx';
await fs.copyFile(source,out+'/build/candidato-v2.pptx');
console.log(JSON.stringify(await finalizePresentation({
 workspaceDir:root,candidatePath:out+'/build/candidato-v2.pptx',finalPath:out+'/BOOSTio-Pitch-3A2-v2-com-roteiro.pptx',
 pythonExecutable:'/Users/trvzera/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',
 integrityValidatorPath:skill+'/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:skill+'/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-bullet-geometry','--validate-heading-fit'],
 explicitTotalSlideCount:17,requiredNativeTableOwnerSlides:[],requiredNativeChartOwnerSlides:[],
 fontPolicy:{basis:'user_request',families:['Lexend','Poppins']},verifyArtifactToolImport:true,
 receiptPath:root+'/materiais/apresentacao/2026-11-10-v2/scripts/validacao-pptx-notas.json'
}),null,2));
