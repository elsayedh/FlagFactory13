# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Jesni Banu (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from datetime import datetime, timedelta

from .calverter import Calverter

from odoo import models, fields, _, api

GENDER_SELECTION = [('male', 'Male'),
                    ('female', 'Female'),
                    ('other', 'Other')]


class HrEmployeeFamilyInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.family'
    _description = 'HR Employee Family'

    employee_id = fields.Many2one('hr.employee', string="Employee", help='Select corresponding Employee',
                                  invisible=1)
    relation_id = fields.Many2one('hr.employee.relation', string="Relation", help="Relationship with the employee")
    member_name = fields.Char(string='Name')
    member_contact = fields.Char(string='Contact No')
    birth_date = fields.Date(string="DOB", tracking=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def mail_reminder(self):
        """Sending expiry date notification for ID and Passport"""

        now = datetime.now() + timedelta(days=1)
        date_now = now.date()
        match = self.search([])
        for i in match:
            if i.id_expiry_date:
                exp_date = fields.Date.from_string(i.id_expiry_date) - timedelta(days=14)
                if date_now >= exp_date:
                    mail_content = "  Hello  " + i.name + ",<br>Your ID " + i.identification_id + "is going to expire on " + \
                                   str(i.id_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('ID-%s Expired On %s') % (i.identification_id, i.id_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()
        match1 = self.search([])
        for i in match1:
            if i.passport_expiry_date:
                exp_date1 = fields.Date.from_string(i.passport_expiry_date) - timedelta(days=180)
                if date_now >= exp_date1:
                    mail_content = "  Hello  " + i.name + ",<br>Your Passport " + i.passport_id + "is going to expire on " + \
                                   str(i.passport_expiry_date) + ". Please renew it before expiry date"
                    main_content = {
                        'subject': _('Passport-%s Expired On %s') % (i.passport_id, i.passport_expiry_date),
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': i.work_email,
                    }
                    self.env['mail.mail'].sudo().create(main_content).send()

    personal_mobile = fields.Char(string='Mobile', related='address_home_id.mobile', store=True,
                  help="Personal mobile number of the employee")
    joining_date = fields.Date(string='Joining Date', help="Employee joining date computed from the contract start date",compute='compute_joining', store=True)
    id_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Identification ID')
    passport_expiry_date = fields.Date(string='Expiry Date', help='Expiry date of Passport ID')
    id_attachment_id = fields.Many2many('ir.attachment', 'id_attachment_rel', 'id_ref', 'attach_ref',
                                        string="Attachment", help='You can attach the copy of your Id')
    passport_attachment_id = fields.Many2many('ir.attachment', 'passport_attachment_rel', 'passport_ref', 'attach_ref1',
                                              string="Attachment",
                                              help='You can attach the copy of Passport')
    fam_ids = fields.One2many('hr.employee.family', 'employee_id', string='Family', help='Family Information')

    passport_expiry_date = fields.Date(string='Passport Expiry Date', help='Expiry date of Passport ID')
    passport_expiry_date_hajri = fields.Char(string='Expiry Date Hajri',compute='_calculate_passport_hajri', help='Expiry date of Passport ID')
    id_expiry_date = fields.Date(string='ID Expiry Date', help='Expiry date of Identification ID')
    id_expiry_date_hajri = fields.Char(string='Expiry Date Hajri',compute='_calculate_id_hajri', help='Expiry date of Identification ID')


    @api.depends('contract_id')
    def compute_joining(self):
        if self.contract_id:
            date = min(self.contract_id.mapped('date_start'))
            self.joining_date = date
        else:
            self.joining_date = False

    @api.onchange('spouse_complete_name', 'spouse_birthdate')
    def onchange_spouse(self):
        relation = self.env.ref('hr_employee_updation.employee_relationship')
        lines_info = []
        spouse_name = self.spouse_complete_name
        date = self.spouse_birthdate
        if spouse_name and date:
            lines_info.append((0, 0, {
                'member_name': spouse_name,
                'relation_id': relation.id,
                'birth_date': date,
            })
                              )
            self.fam_ids = [(6, 0, 0)] + lines_info

    @api.depends('id_expiry_date')
    def _calculate_id_hajri(self):
        cal = Calverter()

        if self.id_expiry_date:
            d = self.id_expiry_date
            jd = cal.gregorian_to_jd(d.year, d.month, d.day)
            # print(jd)
            # print(cal.jd_to_islamic(jd))
            hj = cal.jd_to_islamic(jd)
            # print(hj[0], "/", hj[1], "/", hj[2])
            self.id_expiry_date_hajri =str( hj[2])+ "/"+ str(hj[1])+ "/"+str(hj[0])
        else:
            self.id_expiry_date_hajri =""

    @api.depends('passport_expiry_date')
    def _calculate_passport_hajri(self):
        cal = Calverter()
        if self.passport_expiry_date:
            d = self.passport_expiry_date
            jd = cal.gregorian_to_jd(d.year, d.month, d.day)
            # print(jd)
            # print(cal.jd_to_islamic(jd))
            hj = cal.jd_to_islamic(jd)
            # print(hj[0], "/", hj[1], "/", hj[2])
            self.passport_expiry_date_hajri = str(hj[2]) + "/" + str(hj[1])+ "/" + str(hj[0])
        else:
            self.passport_expiry_date_hajri =""




class EmployeeRelationInfo(models.Model):
    """Table for keep employee family information"""

    _name = 'hr.employee.relation'

    name = fields.Char(string="Relationship", help="Relationship with thw employee")