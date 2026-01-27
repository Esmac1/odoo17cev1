from odoo import models, api

class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, values_list):
        messages = super().create(values_list)
        bus = self.env['bus.bus']
        
        for msg in messages:
            # Skip if no model/res_id (system messages)
            if not msg.model or not msg.res_id:
                continue
                
            try:
                # Get the channel/thread info safely
                record = self.env[msg.model].browse(msg.res_id).exists()
                if not record:
                    continue
                    
                record_name = getattr(record, 'name', getattr(record, 'display_name', 'Unknown'))
                
                # Check if this is a discuss channel (mail.channel in Odoo CE)
                is_discuss_channel = (msg.model == 'mail.channel')
                
                print(f"🔔 DEBUG: Message created - Model: {msg.model}, Channel: {record_name}, is_discuss_channel: {is_discuss_channel}")
                
                # Only send notifications for discuss channels
                if is_discuss_channel:
                    # Send to general channel that frontend listens to
                    bus_channel = "discuss_general_channel"
                    
                    bus.sendone(
                        bus_channel,
                        {
                            'type': 'new_message',
                            'message_id': msg.id,
                            'body': msg.body or '',
                            'author': msg.author_id.name or 'Unknown',
                            'author_id': msg.author_id.id,
                            'model': msg.model,
                            'res_id': msg.res_id,
                            'record_name': record_name,
                            'is_discuss_channel': is_discuss_channel,
                            'timestamp': msg.create_date.isoformat() if msg.create_date else '',
                        }
                    )
                    print(f"🔔 Sent bus notification for message in {record_name}")
                else:
                    print(f"🔔 Skipping non-discuss channel: {msg.model}")
                    
            except Exception as e:
                # Skip if any error occurs
                print(f"🔔 Error sending notification: {e}")
                continue
                
        return messages
