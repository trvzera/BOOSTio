from flask import Blueprint,request,jsonify
from flask_login import login_required,current_user
from utils.limite_requisicoes import limiter, chave_usuario
from models import db
from models.build_salva import LimiteBuildsError, EmailNaoVerificadoError
from sqlalchemy.exc import SQLAlchemyError
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError

from services.build_service.listar_builds_service import ListarBuildService
from services.build_service.criar_build_service import ErroGeracaoBuild
from services.build_service.planejamento_geracao import ErroPlanejamentoBuild
from services.build_service.gerar_build_service import GerarBuildService
from services.build_service.buscar_build_service import BuscarBuildService
from services.build_service.listar_catalogo_build_service import ListarCatalogoBuildService
from services.build_service.criar_build_manual_service import CriarBuildManualService
from services.build_service.atualizar_build_service import AtualizarBuildService
from services.build_service.duplicar_build_service import DuplicarBuildService
from services.build_service.definir_setup_atual_service import DefinirSetupAtualService
from services.build_service.excluir_build_service import ExcluirBuildService
from services.build_service.buscar_build_publica_service import BuscarBuildPublicaService
from services.build_service.copiar_build_publica_service import CopiarBuildPublicaService
from services.llm_service.bloquear_geracao_service import GeracaoEmAndamentoError
from services.llm_service.reservar_chamada_service import CotaGlobalIAError, ControleIAIndisponivelError

build_bp = Blueprint("build",__name__,url_prefix='/build')


class BuildController:
    """Controller HTTP do recurso; métodos estáticos não compartilham estado de requisição."""

    @staticmethod
    @build_bp.errorhandler(EmailNaoVerificadoError)
    def verificar_email_antes_de_criar(erro):
      return jsonify({"erro": str(erro), "codigo": "email-nao-verificado"}),403


    @staticmethod
    @build_bp.errorhandler(LimiteBuildsError)
    def limite_builds(erro):
      return jsonify({"erro": str(erro), "codigo": "limite-builds", "limite": 3}),409


    @staticmethod
    @build_bp.get("/")
    @login_required
    def mostrar_builds():
      try:
        builds = ListarBuildService().executar(current_user.id)
        return jsonify({"builds": builds, "limite": 3}),200
      except ValueError as e:
        return jsonify({"erro": str(e)}),404

    @staticmethod
    @build_bp.post("/")
    @limiter.limit("10 per minute")
    @limiter.limit("60 per day")
    @limiter.limit("10 per day", key_func=chave_usuario)
    @login_required
    def criar_build():
      try:
        dados = request.get_json(silent=True)

        if not isinstance(dados, dict):
          return jsonify({"erro": "Envie um objeto JSON válido"}),400

        usuario_id = current_user.id
        build = GerarBuildService().executar(usuario_id, dados)
        builds = ListarBuildService().executar(usuario_id)

        return jsonify({"mensagem": "Build criada com sucesso", "build": build, "builds": builds}),201
      except (LimiteBuildsError, EmailNaoVerificadoError):
        raise
      except GeracaoEmAndamentoError as erro:
        return jsonify({"erro": str(erro), "codigo": "geracao-em-andamento"}),409
      except CotaGlobalIAError as erro:
        resposta = jsonify({"erro": str(erro), "codigo": "ia-cota-global"})
        resposta.headers["Retry-After"] = str(erro.espera)
        return resposta,429
      except ControleIAIndisponivelError:
        return jsonify({"erro": "A geração está temporariamente indisponível. Tente novamente mais tarde.", "codigo": "ia-controle-indisponivel"}),503
      except ErroGeracaoBuild as erro:
        return jsonify({"erro": str(erro), "codigo": "geracao-invalida", "geracao": erro.geracao}),502
      except ErroPlanejamentoBuild as erro:
        return jsonify({"erro": str(erro), "codigo": "planejamento-invalido", "geracao": erro.geracao}),400
      except ValueError as e:
        return jsonify({"erro": str(e)}),400

      except Timeout:
        return jsonify({"erro": "A IA demorou demais para responder. Suas respostas foram preservadas; tente novamente em alguns instantes.", "codigo": "ia-timeout"}),504
      except ConnectionError:
        return jsonify({"erro": "Não foi possível acessar o serviço de montagem. Tente novamente em alguns instantes.", "codigo": "ia-indisponivel"}),503
      except HTTPError as erro:
        if erro.response is not None and erro.response.status_code == 429:
          resposta = jsonify({"erro": "O serviço de montagem atingiu um limite temporário. Aguarde alguns instantes e tente novamente.", "codigo": "ia-limite"})
          espera = erro.response.headers.get("Retry-After", "")
          if espera.isascii() and espera.isdigit() and len(espera) <= 4 and 0 < int(espera) <= 3600:
            resposta.headers["Retry-After"] = espera
          return resposta,503
        return jsonify({"erro": "O serviço de montagem está indisponível agora. Tente novamente mais tarde.", "codigo": "ia-provedor"}),502
      except RequestException:
        return jsonify({"erro": "Não foi possível consultar o serviço de montagem. Tente novamente em alguns instantes.", "codigo": "ia-provedor"}),502

      except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar a build"}),500

      except Exception:
        return jsonify({"erro": "Erro ao gerar a build"}),500


    @staticmethod
    @build_bp.get("/catalogo")
    @login_required
    def catalogo_build():
      return jsonify({"pecas": ListarCatalogoBuildService().executar()}),200


    @staticmethod
    @build_bp.post("/manual")
    @login_required
    def criar_build_manual():
      try:
        return jsonify({"build": CriarBuildManualService().executar(current_user.id, request.get_json(silent=True))}),201
      except LimiteBuildsError:
        raise
      except ValueError as erro:
        return jsonify({"erro": str(erro)}),400
      except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao salvar a build"}),500


    @staticmethod
    @build_bp.get("/<build_id>")
    @login_required
    def buscar_build(build_id):
      try:
        build = BuscarBuildService().executar(current_user.id, build_id)
        return jsonify({"build": build}),200
      except ValueError as e:
        return jsonify({"erro": str(e)}),404


    @staticmethod
    @build_bp.put("/<build_id>")
    @login_required
    def atualizar_build(build_id):
      try:
        return jsonify({"build": AtualizarBuildService().executar(current_user.id, build_id, request.get_json(silent=True))}),200
      except ValueError as erro:
        return jsonify({"erro": str(erro)}),400
      except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao atualizar a build"}),500


    @staticmethod
    @build_bp.post("/<build_id>/duplicar")
    @login_required
    def duplicar_build(build_id):
      try:
        return jsonify({"build": DuplicarBuildService().executar(current_user.id, build_id)}),201
      except LimiteBuildsError:
        raise
      except ValueError as erro:
        return jsonify({"erro": str(erro)}),400
      except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao duplicar a build"}),500


    @staticmethod
    @build_bp.post("/<build_id>/setup-atual")
    @login_required
    def definir_setup_atual(build_id):
      try:
        DefinirSetupAtualService().executar(current_user.id, build_id)
        return jsonify({"builds": ListarBuildService().executar(current_user.id)}),200
      except ValueError as erro:
        return jsonify({"erro": str(erro)}),404
      except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao definir o setup atual"}),500


    @staticmethod
    @build_bp.delete("/<build_id>")
    @login_required
    def excluir_build(build_id):
      try:
        ExcluirBuildService().executar(current_user.id, build_id)
        return "",204
      except ValueError as erro:
        return jsonify({"erro": str(erro)}),400
      except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Erro ao excluir a build"}),500


    @staticmethod
    @build_bp.get("/<build_id>/publica")
    def buscar_build_publica(build_id):
      try:
        resposta = jsonify({"build": BuscarBuildPublicaService().executar(build_id)})
        resposta.headers["Cache-Control"] = "no-store"
        return resposta,200
      except ValueError as erro:
        resposta = jsonify({"erro": str(erro)})
        resposta.headers["Cache-Control"] = "no-store"
        return resposta,404


    @staticmethod
    @build_bp.post("/<build_id>/copiar-publica")
    @login_required
    def copiar_build_publica(build_id):
      try:
        return jsonify({"build": CopiarBuildPublicaService().executar(current_user.id, build_id)}),201
      except (LimiteBuildsError, EmailNaoVerificadoError):
        raise
      except ValueError as erro:
        return jsonify({"erro": str(erro)}),404
      except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"erro": "Não foi possível salvar a cópia. Tente novamente."}),500
