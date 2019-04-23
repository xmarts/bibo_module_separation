# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, tools
from openerp.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, date, time, timedelta

class TicketNomina( models.Model ):
	_name = 'ticket.nomina'
	_rec_name = 'bar_code'

	id_prod = fields.Many2one( 'mrp.production','Operacion' )
	tic_emp = fields.Many2one( 'hr.employee' , 'Empleado')

	id_product_product = fields.Many2one( 'product.product', 'Producto marcado como mano de obra: ', invisible=True)

	bar_code = fields.Char( string = 'Codigo de barras' )
	name_ope = fields.Char( string = 'Nombre de operación' )
	ref_prod = fields.Many2one('product.template' , string = 'Producto' , related='id_prod.product_id.product_tmpl_id')
	date_rea = fields.Date( string = 'Fecha de creación' )
	date_lec = fields.Date( string = 'Fecha de lectura' )
	can_prod = fields.Integer( string = 'Cantidad de producto' )
	cost_tot = fields.Float( string = 'Costo total' )
	hand_ope = fields.Char( string = 'Mano de obra' )

class Modules(models.Model):
	_name = 'tk.modules'

	name_mod = fields.Char( string = 'Nombre del modulo' )
	_rec_name = 'name_mod'

class AddTicketEmployee(models.TransientModel):
	_name = 'ticket.employee'

	name = fields.Char(string="Asignacion", readonly=True, required=True, copy=False, default='Nuevo')
	employee = fields.Many2one( 'hr.employee' , string = 'Empleado' )
	busc_bar = fields.Char( string = 'Codigo de barras' )
	sele_fec = fields.Date( string = 'Selecciona la fecha' )
	mensaje = fields.Char(string="",readonly=True)
	comprobacion_error = fields.Boolean(string='Comprobacion error', default = False, compute='to_unlock')

	@api.onchange('busc_bar')
	def search_tickets(self):
		asignado = False
		mensaje = ''
		if self.comprobacion_error == True:
			raise UserError('Revisa los campos, o que el ticket no este asignado a un colaborador. Presiona el boton "Desbloquear", para continuar.')
		else:
			if self.busc_bar and self.employee and self.sele_fec:
				res = self.env['ticket.nomina'].search([('bar_code', '=', self.busc_bar)], limit=1)
				if res:
					if not res.tic_emp:
						res.write({'tic_emp': self.employee.id})
						res.write({'date_lec': self.sele_fec})
						asignado = True
					if res.tic_emp:
						self.busc_bar=''
						mensaje = 'El ticket '+ res.bar_code +' ya tiene asignado al empleado '+res.tic_emp.name
						self.comprobacion_error = True	
				else:
					self.busc_bar=''
					mensaje = 'Sin resultados'
			else:
				mensaje = 'Completa los campos'

		if asignado == True:
			self.busc_bar=''
			mensaje ='El Ticket ' + " " + res.bar_code + ' fue asignado a ' + " " + res.tic_emp.name

		if mensaje != '':
			self.mensaje= mensaje
			self.busc_bar=''

	@api.one
	@api.depends('comprobacion_error')
	def to_unlock(self):
		self.comprobacion_error = False

class AddCampModules(models.Model):
	_inherit = 'mrp.production'

	mod_prod = fields.Many2one( 'tk.modules' , string = 'Modulo' )

	prod_id = fields.One2many('ticket.nomina', 'id_prod' , 'Codigo de produccion' )

	tic_gen = fields.Boolean( string = 'Tickets generados', default = False )

	@api.multi
	@api.depends('move_raw_ids')
	def imp_ticket(self, code):
		if self.tic_gen == False:
			self.tic_gen = True
			if self.move_raw_ids:
				camp_date = fields.Date.today()
				cost_tota = self.product_qty * self.product_id.standard_price
				inv_obj = self.env['ticket.nomina']
				self.ensure_one()
				invoice = ''
				i=0
				for xn in self.move_raw_ids:
					if xn.product_id.hand_work_prod:
						i+=1
						val = 0
						if i > 100:
							val = str(i)
						elif i > 9:
							val = '0' + str(i)
						else:
							val = '00' + str(i)
						invoice = inv_obj.create({
								'id_prod'  : self.id,
								'bar_code' : self.name + val,
								'name_ope' : 'Mano de obra',
								'hand_ope' : xn.product_id.name,
								'ref_prod' : self.product_id.product_tmpl_id,
								'date_rea' : camp_date,
								'can_prod' : self.product_qty,
								'cost_tot' : self.product_qty * xn.product_id.standard_price,
								'id_product_product' : xn.product_id.id
							})
			else:
				raise UserError('Sin datos')
		else:
			raise UserError('Los tickets ya han sido generados')

		if invoice != '':
			return invoice
		else:
			raise UserError('No hay elementos marcados como mano de obra')

class AddCampHandWork(models.Model):
	_inherit = 'product.template'

	hand_work = fields.Boolean( string = 'Mano de obra' )

class AddCampHandWorkProd(models.Model):
	_inherit = 'product.product'

	hand_work_prod = fields.Boolean( string = 'Mano de obra', related='product_tmpl_id.hand_work' )

