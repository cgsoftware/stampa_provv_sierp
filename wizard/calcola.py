import wizard
import decimal_precision as dp
import pooler
import time
from tools.translate import _
from osv import osv, fields
from tools.translate import _

class tempstatistiche_proviggioni(osv.osv):
    def _pulisci(self,cr,uid,context):
        ids = self.search(cr,uid,[])
        ok = self.unlink(cr,uid,ids,context)
        return True
    
    _name = 'tempstatistiche.proviggioni'
    _description = 'Temporaneo Stampa Proviggioni'
    _columns = {'name':fields.many2one('fiscaldoc.header', 'Documento', required=True),
                'imponibile':fields.float('Imponibile', digits=(12,2)),
                'prov':fields.float('Proviggione', digits=(3, 2)),
                'perc':fields.float('Percentuale', digits=(12,2)),
                
            }
    
    
    def carica_doc(self, cr,uid,parametri,context):
        ok = self._pulisci(cr, uid, context)
        testa = self.pool.get('fiscaldoc.header')
        filtro_data = [('data_documento','<=', parametri.adata),('data_documento','>=', parametri.dadata)]
        testate_ids = testa.search(cr, uid, filtro_data)
        lista_id = []
        filtro1 = [('tipo_documento', 'in', ('FA','FI','FD'))]
        idsTipoDoc = self.pool.get('fiscaldoc.causalidoc').search(cr, uid, filtro1)
        idsTipoDoc = tuple(idsTipoDoc)
        if testate_ids:
            for rec_testa in testa.browse(cr, uid, testate_ids):
              if rec_testa.tipo_doc.id in idsTipoDoc:
                  
                  if rec_testa.partner_id.agent_id:
                   #import pdb;pdb.set_trace()   
                   if rec_testa.partner_id.agent_id.partner_id.id == parametri.agente.id:
                    #CONTROLLO CHE IL DOCUMENTO NON ABBIA SCONTO PAGAMENTO
                    #IN QUESTO CASO POSSO CALCOLARE IL TOTALE
                    #SUL NETTO MERCE
                    
                    if not rec_testa.sconto_pagamento or rec_testa.sconto_partner:
                        for riga_doc in rec_testa.righe_articoli:
                            #RIGA GIA' ESISTENTE
                            cerca = [('name','=',rec_testa.id)]
                            id_temp = self.search(cr,uid,cerca)
                            if id_temp:
                                riga_temp = self.browse(cr,uid,id_temp)[0]
                                imponibile = riga_temp.imponibile+riga_doc.totale_riga
                                rigawr ={'imponibile':imponibile,
                                         'prov':imponibile*riga_doc.perc_provv/100,
                                         'perc':riga_doc.perc_provv
                                        }
                                ok = self.write(cr,uid,id_temp,rigawr)
                            else:
                                imponibile = riga_doc.totale_riga
                                rigawr={'name':rec_testa.id,
                                        'imponibile':imponibile,
                                        'prov2':imponibile*riga_doc.perc_provv/100,
                                        'perc':riga_doc.perc_provv,
                                        }
                                #import pdb;pdb.set_trace()  
                                ok = self.create(cr,uid,rigawr)
                    else:
                        for riga_doc in rec_testa.righe_articoli:
                            #RIGA GIA' ESISTENTE
                            cerca = [('name','=',rec_testa.id)]
                            id_temp = self.search(cr,uid,cerca)
                            if id_temp:
                                riga_temp = self.browse(cr,uid,id_temp)[0]
                                netto = riga_doc.totale_riga
                                if rec_testa.sconto_pagamento:
                                    netto = netto-(netto*riga_doc.sconto_pagamneto/100)
                                    imponibile = riga_temp.imponibile+netto 
                                    rigawr ={'imponibile':imponibile,
                                             'prov':imponibile*riga_doc.perc_provv/100,
                                             'perc':riga_doc.perc_provv
                                             }
                                    ok = self.write(cr,uid,id_temp,rigawr)
                                    
                                if rec_testa.sconto_partner:  
                                    netto = netto-(netto*riga_doc.sconto_partner/100)
                                    imponibile = riga_temp.imponibile+netto 
                                    rigawr ={'imponibile':imponibile,
                                             'prov':imponibile*riga_doc.perc_provv/100,
                                             'perc':riga_doc.perc_provv
                                             }
                                    ok = self.write(cr,uid,id_temp,rigawr)
                            else:
                                netto = riga_doc.totale_riga
                                if rec_testa.sconto_pagamento:
                                    netto = netto-(netto*riga_doc.sconto_pagamneto/100)
                                    rigawr={'name':rec_testa.id,
                                            'imponibile':netto,
                                            'prov':netto*riga_doc.perc_provv/100,
                                            'perc':riga_doc.perc_provv,
                                            }
                                    ok = self.create(cr,uid,rigawr)
                                if rec_testa.sconto_partner:  
                                    netto = netto-(netto*riga_doc.sconto_partner/100)
                                    rigawr={'name':rec_testa.id,
                                            'imponibile':netto,
                                            'prov':netto*riga_doc.perc_provv/100,
                                            'perc':riga_doc.perc_provv,
                                            }
                                    ok = self.create(cr,uid,rigawr)
tempstatistiche_proviggioni()
                


class parcalcolo_proviggioni(osv.osv_memory):
    _name ='parcalcolo.proviggioni'
    _description = 'paramentri per il calcolo delle proviggioni agente'
    _columns = {'dadata': fields.date('Da Data Documento', required=True  ),
                'adata': fields.date('A Data Documento', required=True),
                'agente':fields.many2one('res.partner', 'Agente', required=True),
                }
    def _build_contexts(self, cr, uid, ids, data, parametri, context=None):
        if context is None:
            context = {}
        result = {}
       
        #if data['form']['tipodoc']==0 or data['form']['tipodoc']==False:
        #     data['form']['tipodoc']=1
        #     data['form']['atipodoc']=99999
        #import pdb;pdb.set_trace()
        #CONVERTE LA DATA IN FORMATO GG/MM/AAAA
        parametri.dadata = (parametri.dadata, "%Y-%m-%d")
        parametri.dadata=time.strftime("%d/%m/%Y",parametri.dadata)
        
        parametri.adata = time.strptime(parametri.adata, "%Y-%m-%d")
        parametri.adata=time.strftime("%d/%m/%Y",parametri.adata)
        
        result = {'dadata':parametri.dadata,'adata':parametri.adata, 'agente':parametri.agente.name
                  #'tipo_Stampa':parametri.tipo_Stampa
                  #'tipodoc':data['form']['tipodoc'],'atipodoc':data['form']['atipodoc'],
                  
                    }
        #import pdb;pdb.set_trace()
        return result
    
    def _print_report(self, cr, uid, ids, data, parametri, context=None):
       
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['dadata',  'adata', 'agente'])[0] #  'tipodoc', 'atipodoc' 
        used_context = self._build_contexts(cr, uid, ids, data, parametri, context=context)
        #import pdb;pdb.set_trace()
        data['form']['parameters'] = used_context
        pool = pooler.get_pool(cr.dbname)
        #fatture = pool.get('fiscaldoc.header')
        active_ids = context and context.get('active_ids', [])
        Primo = True
        return {'type': 'ir.actions.report.xml',
                'report_name': 'provvigioni',
                'datas': data,
                }
        
    def crea_temp(self, cr, uid, ids, data, context=None):
        righe = self.pool.get('fiscaldoc.righe')
        testa = self.pool.get('fiscaldoc.header')
        parametri = self.browse(cr,uid,ids)[0]
        ok = self.pool.get('tempstatistiche.proviggioni').carica_doc(cr,uid,parametri,context)
        return self._print_report(cr, uid, ids, data, parametri, context=context)
parcalcolo_proviggioni()

#class parcalcolo_categorie(osv.osv_memory):
#    _name = 'parcalcolo.categorie' 
#    _description = 'parametri di selezione categorie da escludere'
#    _columns = {'name':fields.many2one('parcalcolo.trasporti','Testata parametri'),
#                'categoria':fields.many2one('product.category', 'Categorie da escludere', required=True,),
#                }
#parcalcolo_categorie()

#class parcalcolo_causale(osv.osv_memory):
#    _name = 'parcalcolo.causale' 
#    _description = 'parametri di selezione categorie da escludere'
#    _columns = {'name':fields.many2one('parcalcolo.trasporti','Testata Causali'),
#                'causale':fields.many2one('fiscaldoc.causalidoc', 'Causali da includere',)
#                }
#parcalcolo_causale()