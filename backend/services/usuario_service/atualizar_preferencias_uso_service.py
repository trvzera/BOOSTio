from models import db, Usuario, PreferenciasUso


class AtualizarPreferenciasUsoService:
    NIVEIS = {"iniciante", "intermediario", "experiente"}

    def executar(self, usuario_id, dados):
        if not isinstance(dados, dict) or not dados or set(dados) - {"nivel_hardware", "tutorial"}:
            raise ValueError("Informe apenas o nível de conhecimento ou a conclusão do tutorial.")
        nivel = dados.get("nivel_hardware")
        if nivel is not None and (not isinstance(nivel, str) or nivel not in self.NIVEIS):
            raise ValueError("Escolha um nível de conhecimento válido.")
        if "tutorial" in dados and (not isinstance(dados["tutorial"], str) or dados["tutorial"] not in {"concluido", "pulado"}):
            raise ValueError("Informe se o tutorial foi concluído ou pulado.")
        usuario = Usuario.buscar_por_id(usuario_id)
        if usuario is None:
            return None
        if usuario.preferencias_uso is None:
            usuario.preferencias_uso = PreferenciasUso(tutorial="nao-oferecido")
        if "nivel_hardware" in dados:
            usuario.preferencias_uso.nivel_hardware = nivel
        if "tutorial" in dados:
            usuario.preferencias_uso.tutorial = dados["tutorial"]
            usuario.preferencias_uso.versao_tutorial = 1
        db.session.commit()
        return usuario.to_dict(incluir_budget=True, incluir_preferencias=True)
