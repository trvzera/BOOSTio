from decimal import Decimal, InvalidOperation


class PlanejarPotenciaService:
    VERSAO='reserva_auxiliares_v1'
    RESERVAS={'placa_mae':50,'memoria_ram':10,'ssd':15,'hd':30,'fan':10,
              'air_cooler':30,'water_cooler':60,'gabinete':20}
    EXTERNOS={'fonte','monitor','teclado','mouse','fone','cabo_rede','adaptador_wifi','webcam','microfone'}
    MARGEM=Decimal('1.20')

    @staticmethod
    def numero(v):
        if v is None or isinstance(v,bool):return None
        try:
            n=Decimal(str(v))
            return n if n.is_finite() and n>=0 else None
        except (ValueError,InvalidOperation):return None

    def executar(self,itens):
        conhecido=Decimal(0);reservado=Decimal(0);estimativas=[];desconhecidos=[];internos=0
        for tipo,item,peca in itens:
            if tipo in self.EXTERNOS:continue
            internos+=1;peca=peca or {};q=self.numero(item.get('quantidade',1))
            if q is None or q<1 or q!=int(q):
                desconhecidos.append(tipo+':quantidade');continue
            consumo=self.numero(peca.get('consumo_energia'))
            if tipo in ('processador','placa_video') and consumo == 0:
                consumo=None
            if consumo is not None:
                conhecido+=consumo*q;continue
            if not peca or tipo not in self.RESERVAS:
                desconhecidos.append(tipo+':consumo');continue
            unidades=q
            if tipo in ('memoria_ram','fan'):
                campo='quantidade_pentes' if tipo=='memoria_ram' else 'quantidade'
                fisicas=self.numero(peca.get(campo))
                if fisicas is None or fisicas<1 or fisicas!=int(fisicas):
                    desconhecidos.append(tipo+':'+campo);continue
                unidades*=fisicas
            watts=Decimal(self.RESERVAS[tipo])*unidades;reservado+=watts
            estimativas.append(dict(categoria=tipo,unidades=int(unidades),watts_por_unidade=self.RESERVAS[tipo],reserva_w=float(watts)))
        total=conhecido+reservado
        return dict(versao=self.VERSAO,consumo_conhecido_w=float(conhecido),reserva_w=float(reservado),
          total_planejado_w=float(total) if internos and not desconhecidos else None,
          potencia_minima_w=float(total*self.MARGEM) if internos and not desconhecidos else None,
          margem_percentual=20,estimativas=estimativas,desconhecidos=desconhecidos)
